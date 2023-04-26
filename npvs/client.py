import socket

from npvs import rtp
from npvs import rtsp
from npvs.common import *
from npvs.media_player import MediaPlayer
from npvs.ps_receiver import PsReceiver
from npvs.video import VideoAssembler


class Client(MediaPlayer):
    def __init__(self, serverIp: str, serverRtspPort: int, fileName: str) -> None:
        super().__init__()

        self.logger = get_logger("client")

        self.serverIp = serverIp
        self.serverRtspPort = serverRtspPort
        self.fileName = fileName

        self.clientRtpPort = 0
        self.rtpSocket: socket.socket = None
        self.packetReceiver = PsReceiver()

        self.videoAssembler = VideoAssembler()

        self.psReceiver = PsReceiver(self.serverIp, self.logger)
        self.CSeq = 0
        self.session = -1

    def __del__(self) -> None:
        self.teardown()
        self.rtspSocket.close()

    def send_RTSP_request(self, method: rtsp.Method) -> bool:
        self.CSeq += 1

        request = {
            "method": method,
            "fileName": self.fileName,
            "CSeq": self.CSeq,
        }
        if method == rtsp.Method.SETUP:
            request["clientPort"] = self.clientRtpPort
        else:
            request["session"] = self.session
        message = rtsp.create_request(request)
        self.rtspSocket.sendall(message.encode())

        message = self.rtspSocket.recv(rtsp.RTSP_MESSAGE_SIZE).decode()
        self.respond = rtsp.parse_response(message)
        if self.respond["statusCode"] > 299:
            log(self.respond["statusCode"], "server responded")
            return False

        return True

    def _setup_(self) -> bool:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        self.clientRtpPort = int(s.getsockname()[1])  # get the port
        s.listen()

        if not self.send_RTSP_request(rtsp.Method.SETUP):
            self.rtpSocket.close()
            return False

        self.session = self.respond["session"]
        self.rtpSocket, _ = s.accept()
        self.rtpSocket.settimeout(0.5)

        return True

    def _play_(self) -> bool:
        return self.send_RTSP_request(rtsp.Method.PLAY)

    def _pause_(self) -> bool:
        return self.send_RTSP_request(rtsp.Method.PAUSE)

    def _teardown_(self) -> bool:
        if not self.send_RTSP_request(rtsp.Method.TEARDOWN):
            return False
        self.rtpSocket.close()
        return True

    def _stream_(self) -> None:
        if self.packetSizeQueue.empty():
            return

        size = self.packetSizeQueue.get()
        data = self.rtpBuffer.readIfEnough(size)
        self.videoAssembler.add_packet(rtp.decode(data))

    def next_frame(self):
        return self.videoAssembler.next_frame()
