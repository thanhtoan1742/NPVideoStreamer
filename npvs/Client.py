import socket

import Rtp
import Rtsp
from common import *
from MediaPlayer import MediaPlayer
from PsReceiver import PsReceiver
from Video import VideoAssembler


class Client(MediaPlayer):
    def __init__(self, serverIp: str, serverRtspPort: int, fileName: str) -> None:
        super().__init__()

        self.logger = getLogger("client")

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

    def sendRtspRequest(self, method: Rtsp.Method) -> bool:
        self.CSeq += 1

        request = {
            "method": method,
            "fileName": self.fileName,
            "CSeq": self.CSeq,
        }
        if method == Rtsp.Method.SETUP:
            request["clientPort"] = self.clientRtpPort
        else:
            request["session"] = self.session
        message = Rtsp.createRequest(request)
        self.rtspSocket.sendall(message.encode())

        message = self.rtspSocket.recv(Rtsp.RTSP_MESSAGE_SIZE).decode()
        self.respond = Rtsp.parseRespond(message)
        if self.respond["statusCode"] > 299:
            log(self.respond["statusCode"], "server responded")
            return False

        return True

    def _setup_(self) -> bool:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        self.clientRtpPort = int(s.getsockname()[1])  # get the port
        s.listen()

        if not self.sendRtspRequest(Rtsp.Method.SETUP):
            self.rtpSocket.close()
            return False

        self.session = self.respond["session"]
        self.rtpSocket, _ = s.accept()
        self.rtpSocket.settimeout(0.5)

        return True

    def _play_(self) -> bool:
        return self.sendRtspRequest(Rtsp.Method.PLAY)

    def _pause_(self) -> bool:
        return self.sendRtspRequest(Rtsp.Method.PAUSE)

    def _teardown_(self) -> bool:
        if not self.sendRtspRequest(Rtsp.Method.TEARDOWN):
            return False
        self.rtpSocket.close()
        return True

    def _stream_(self) -> None:
        if self.packetSizeQueue.empty():
            return

        size = self.packetSizeQueue.get()
        data = self.rtpBuffer.readIfEnough(size)
        self.videoAssembler.addPacket(Rtp.decode(data))

    def nextFrame(self):
        return self.videoAssembler.nextFrame()
