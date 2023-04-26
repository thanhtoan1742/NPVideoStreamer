import socket

from npvs import rtp, rtsp
from npvs.common import *
from npvs.media_player import MediaPlayer
from npvs.ps_receiver import PsReceiver
from npvs.video import VideoAssembler


class Client(MediaPlayer):
    def __init__(self, ip: str, rtsp_port: int, filename: str) -> None:
        super().__init__()

        self.logger = get_logger("client")

        self.ip = ip
        self.rtsp_port = rtsp_port
        self.filename = filename

        self.rtp_port = 0
        self.rtsp_socket: socket.socket = None

        self.video_assembler = VideoAssembler()

        self.ps_receiver = PsReceiver(self.ip, self.logger)
        self.cseq = 0
        self.session = -1

    def __del__(self) -> None:
        self.teardown()
        self.rtsp_socket.close()

    def send_RTSP_request(self, method: rtsp.Method) -> bool:
        self.cseq += 1

        request = {
            "method": method,
            "fileName": self.filename,
            "CSeq": self.cseq,
        }
        if method == rtsp.Method.SETUP:
            request["clientPort"] = self.rtp_port
        else:
            request["session"] = self.session
        message = rtsp.create_request(request)
        self.rtsp_socket.sendall(message.encode())

        message = self.rtsp_socket.recv(rtsp.RTSP_MESSAGE_SIZE).decode()
        self.respond = rtsp.parse_response(message)
        if self.respond["statusCode"] > 299:
            log(self.respond["statusCode"], "server responded")
            return False

        return True

    def _setup_(self) -> bool:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        self.rtp_port = int(s.getsockname()[1])  # get the port
        s.listen()

        if not self.send_RTSP_request(rtsp.Method.SETUP):
            self.rtsp_socket.close()
            return False

        self.session = self.respond["session"]
        self.rtsp_socket, _ = s.accept()
        self.rtsp_socket.settimeout(0.5)

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
        if self.packetSizeQueue.empty():
            return

        size = self.packetSizeQueue.get()
        data = self.rtpBuffer.readIfEnough(size)
        self.video_assembler.add_packet(rtp.decode(data))

    def next_frame(self):
        return self.video_assembler.next_frame()
