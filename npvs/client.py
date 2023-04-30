import cProfile
import json
import pstats
import socket

from npvs import rtp, rtsp
from npvs.common import *
from npvs.media_player import MediaPlayer
from npvs.ps_receiver import PsReceiver
from npvs.video import VideoAssembler


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

        self.video_assembler = VideoAssembler()

        self.rtp_socket: socket.socket = None
        self.client_rtp_port = 0
        self.ps_receiver: PsReceiver = None

    def __del__(self) -> None:
        self.teardown()
        self.rtsp_socket.close()
        self.logger.info("client done")

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
        self.logger.info("sent message = %s", json.dumps(request, indent=2))

        message = self.rtsp_socket.recv(rtsp.RTSP_MESSAGE_SIZE).decode()
        self.response = rtsp.parse_response(message)
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
        self.client_rtp_port = int(s.getsockname()[1])  # get the port
        s.listen()

        if not self.send_RTSP_request(rtsp.Method.SETUP):
            s.close()
            return False

        self.rtsp_session = self.response["session"]
        self.rtp_socket, _ = s.accept()
        self.ps_receiver = PsReceiver(self.rtp_socket)

        s.close()
        return True

    def _play_(self) -> bool:
        return self.send_RTSP_request(rtsp.Method.PLAY)

    def _pause_(self) -> bool:
        return self.send_RTSP_request(rtsp.Method.PAUSE)

    def _teardown_(self) -> bool:
        if not self.send_RTSP_request(rtsp.Method.TEARDOWN):
            return False
        self.rtsp_socket.close()
        return True

    def _stream_(self) -> None:
        # self.logger.debug("_stream_ called")
        try:
            payload = self.ps_receiver.next_payload()
            if not payload:
                return
            self.video_assembler.add_packet(rtp.decode(payload))
        except Exception as e:
            self.logger.error(
                "got exception in _stream_, e = %s, type = %s", str(e), e.__class__
            )
            raise e

    def next_frame(self):
        return self.video_assembler.next_frame()
