import cProfile
import json
import pstats
import socket
from multiprocessing import Process, Queue, Event

from npvs import rtp, rtsp
from npvs.common import *
from npvs.media_player import MediaPlayer
from npvs.ps_receiver import PsReceiver
from npvs.video import VideoAssembler


PACKET_PER_CHECK = 300


def receive_assemble_packet(
    conn: socket.socket,
    frame_queue: Queue,
    stop_flag: Event,
):
    logger = get_logger("receive-assemble-process")
    # logger.setLevel(logging.DEBUG)

    ps_receiver = PsReceiver(conn)
    video_assembler = VideoAssembler(frame_queue)
    packet_counter = 0
    logger.debug("start receiving and assembling")
    while True:
        if packet_counter % PACKET_PER_CHECK == 0:
            logger.debug("checking stop flag")
            if stop_flag.is_set():
                logger.debug("stop flag is set, exiting")
                break
            logger.debug("stop flag is not set, continue")
        payload = ps_receiver.next_payload()
        if not payload:
            logger.info("no payload, exiting")
            break
        video_assembler.add_packet(rtp.decode(payload))
        packet_counter += 1
    # frame_queue.close()
    logger.info("receive assemble process is done, exiting")


class Client(MediaPlayer):
    def __init__(self, server_ip: str, server_rtsp_port: int, filename: str) -> None:
        super().__init__()

        self.logger = get_logger("client")
        # self.logger.setLevel(logging.DEBUG)
        self.logger.info(
            "client created, connecting to RTSP(%s, %s)", server_ip, server_rtsp_port
        )

        self.filename = filename

        self.server_ip = server_ip
        self.server_rtsp_port = server_rtsp_port
        self.rtsp_cseq = 0
        self.rtsp_session = -1
        self.rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtsp_socket.connect((self.server_ip, self.server_rtsp_port))
        self.logger.info("connected to RTSP(%s, %s)", server_ip, server_rtsp_port)

        self.rtp_socket: socket.socket = None
        self.frame_queue = Queue()
        self.rtp_process: Process = None
        self.rtp_stop_flag = Event()

    def join_rtp_process(self):
        self.rtp_stop_flag.set()
        self.logger.debug("rtp stop flag is set")
        while not self.frame_queue.empty():
            self.frame_queue.get()
        self.logger.debug("frame queue cleared")
        if self.rtp_process != None:
            self.rtp_process.join(2)
            if self.rtp_process.is_alive():
                self.logger.error(
                    "RTP Process still alive, pid = %d", self.rtp_process.pid
                )
        self.logger.debug("rtp process joined")
        self.rtp_process = None
        if self.rtp_socket != None:
            self.rtp_socket.close()
        self.logger.debug("rtp socket closed")
        self.rtp_socket = None

    def __del__(self) -> None:
        self.logger.debug("client destructor called")
        self.teardown()
        self.join_rtp_process()
        self.rtsp_socket.close()
        self.logger.debug("client done")

    def send_RTSP_request(self, method: rtsp.Method) -> bool:
        self.rtsp_cseq += 1

        request = {
            "method": method,
            "fileName": self.filename,
            "CSeq": self.rtsp_cseq,
        }
        if method == rtsp.Method.SETUP:
            request["clientPort"] = self.client_rtp_port
        else:
            request["session"] = self.rtsp_session
        message = rtsp.create_request(request)
        self.rtsp_socket.sendall(message.encode())
        self.logger.info("sent RTPS message = \n%s", message)

        message = self.rtsp_socket.recv(rtsp.RTSP_MESSAGE_SIZE).decode()
        self.response = rtsp.parse_response(message)
        self.logger.info("received RTPS message = \n%s", message)
        if self.response["statusCode"] > 299:
            self.logger.error(
                "server responsed, status code = %s,\nreponse = %s",
                self.response["statusCode"],
                json.dumps(self.response, indent=2),
            )
            return False

        return True

    def _setup_(self) -> bool:
        # TODO: don't need to make new socket every time we initiate a
        # RTP connection.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        self.client_rtp_port = int(s.getsockname()[1])
        s.listen(1)

        if not self.send_RTSP_request(rtsp.Method.SETUP):
            s.close()
            return False

        self.rtsp_session = self.response["session"]
        self.rtp_socket, _ = s.accept()
        self.rtp_process = Process(
            target=receive_assemble_packet,
            args=[self.rtp_socket, self.frame_queue, self.rtp_stop_flag],
        )
        self.rtp_process.start()

        s.close()
        return True

    def _play_(self) -> bool:
        return self.send_RTSP_request(rtsp.Method.PLAY)

    def _pause_(self) -> bool:
        return self.send_RTSP_request(rtsp.Method.PAUSE)

    def _teardown_(self) -> bool:
        if not self.send_RTSP_request(rtsp.Method.TEARDOWN):
            return False
        self.join_rtp_process()
        return True

    def next_frame(self):
        if self.frame_queue.empty():
            return False, None
        else:
            return True, self.frame_queue.get()
