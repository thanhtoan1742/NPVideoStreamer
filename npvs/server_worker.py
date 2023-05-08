import json
import pickle
import socket
from multiprocessing import Event, Process
from random import randint

from npvs import ps, rtp, rtsp
from npvs.common import *
from npvs.media_player import MediaPlayer
from npvs.video import VideoReader, fit_payload_grey as fit_payload

FRAME_PER_CHECK = 50


def run_server_worker(
    rtsp_socket: socket.socket, client_ip: str, client_rtsp_port: int
):
    worker = ServerWorker(rtsp_socket, client_ip, client_rtsp_port)
    worker.run()
    rtsp_socket.close()


def stream_video(
    client_ip: str,
    client_rtp_port: int,
    filename: str,
    streaming_flag: Event,
    stop_flag: Event,
):
    logger = get_logger("server-worker-stream")
    # logger.setLevel(logging.DEBUG)

    video_reader = VideoReader(filename)
    connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    rtp_sequence_number = 0
    is_done = False
    while True:
        if is_done:
            break
        if video_reader.frame_counter % FRAME_PER_CHECK == 0:
            if stop_flag.is_set():
                logger.info("stop flag is set, exiting stream process")
                break
            if not streaming_flag.is_set():
                ok = streaming_flag.wait(1)
                if not ok:
                    continue

        ok, frame = video_reader.next_frame()
        if not ok:
            logger.info("video reader done reading, exiting")
            break

        data = {
            "version": 2,
            # "padding": 0, # does not support padding, defaults to 0
            # "extension": 0, # does not support extension, defaults to 0
            # "csrcCount": 0, # does not support other than 0
            "marker": 1,
            "payloadType": 26,  # MJPEG type
            "timestamp": video_reader.frame_counter - 1,
            "ssrc": 123,
            # "csrcList": [], # does not support other than empty list
            "sequenceNumber": rtp_sequence_number,
            "payload": pickle.dumps(fit_payload(frame)),
        }
        rtp_sequence_number += 1

        rtp_packet = rtp.packet_from_dict(data)
        packet = ps.Packet(rtp_packet.encode())
        try:
            connection.sendto(packet.encode(), (client_ip, client_rtp_port))
        except ConnectionResetError as e:
            logger.error(str(e))
            is_done = True
            break
        except Exception as e:
            logger.error("Expcetion when try to send RTP data, e = %s", str(e))
            raise e

    connection.close()


class ServerWorker(MediaPlayer):
    def __init__(
        self, rtsp_socket: socket.socket, client_ip: str, client_rtsp_port: int
    ) -> None:
        super().__init__()
        self.logger = get_logger("server-worker")
        # self.logger.setLevel(logging.DEBUG)
        self.logger.info(
            "server worker created, serving (%s, %s)", client_ip, client_rtsp_port
        )

        self.rtsp_socket = rtsp_socket
        self.client_ip = client_ip
        self.client_rtsp_port = client_rtsp_port
        self.rtsp_session = 0
        self.request: dict = None

        self.stream_process: Process = None
        self.streaming_flag = Event()
        self.stop_flag = Event()

    def __del__(self) -> None:
        if self.stream_process != None:
            self.stream_process.join()

    def send_RTSP_response(self, status_code: rtsp.StatusCode) -> None:
        """Send RTSP response to the client."""
        response = {"statusCode": status_code, "CSeq": self.request["CSeq"]}
        if status_code == rtsp.StatusCode.OK:
            response["session"] = self.rtsp_session
        message = rtsp.create_response(response)

        self.rtsp_socket.send(message.encode())
        self.logger.info("sent RTPS message = \n%s", message)

    def _setup_(self) -> bool:
        # TODO: handle file not found case
        self.rtsp_session = randint(100000, 999999)
        self.stream_process = Process(
            target=stream_video,
            args=[
                self.client_ip,
                self.request["clientPort"],
                self.request["fileName"],
                self.streaming_flag,
                self.stop_flag,
            ],
        )
        self.stream_process.start()

        self.send_RTSP_response(rtsp.StatusCode.OK)
        return True

    def _play_(self) -> bool:
        self.send_RTSP_response(rtsp.StatusCode.OK)
        self.streaming_flag.set()
        return True

    def _pause_(self) -> bool:
        self.send_RTSP_response(rtsp.StatusCode.OK)
        self.streaming_flag.clear()
        return True

    def _teardown_(self) -> bool:
        self.send_RTSP_response(rtsp.StatusCode.OK)
        self.stop_flag.set()
        self.stream_process.join()
        self.stream_process = None
        return True

    def run(self) -> None:
        while True:
            # TODO: handle receiving incomplete message.
            message = self.rtsp_socket.recv(rtsp.RTSP_MESSAGE_SIZE)
            if not message:
                break
            self.logger.info("received RTPS message = \n%s", message.decode())
            self.request = rtsp.parse_request(message.decode())
            if self.request["method"] == rtsp.Method.SETUP:
                self.setup()
            if self.request["method"] == rtsp.Method.PLAY:
                self.play()
            if self.request["method"] == rtsp.Method.PAUSE:
                self.pause()
            if self.request["method"] == rtsp.Method.TEARDOWN:
                self.teardown()
                break
