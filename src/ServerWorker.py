from random import randint
import socket
import numpy as np
import pickle

from common import *
from MediaPlayer import MediaPlayer
from AtomicCounter import AtomicCounter
from Video import VideoReader
import Rtsp, Rtp



class ServerWorker(MediaPlayer):
    def __init__(self, rtspSocket: socket.socket, clientIp: str, clientRtspPort: int) -> None:
        super().__init__()

        self.rtspSocket = rtspSocket
        self.clientIp = clientIp
        self.clientRtspPort = clientRtspPort

        self.session = 0

        self.videoReader: VideoReader = None
        self.frameCounter = AtomicCounter()

        self.clientRtpPort = 0
        self.rtpSocket = None
        self.rtpSequenceNumber = AtomicCounter()

        self.request = None


    def __del__(self) -> None:
        pass

    def sendRtspRespond(self, statusCode: Rtsp.StatusCode, isSetup: bool = False) -> None:
        """Send RTSP reply to the client."""
        respond = {
            "statusCode": statusCode,
            "CSeq": self.request["CSeq"]
        }
        if statusCode == Rtsp.StatusCode.OK:
            respond["session"] = self.session
        message = Rtsp.createRespond(respond)

        self.rtspSocket.send(message.encode())

    def processRtspRequest(self, message: str) -> None:
        """Process RTSP request sent from the client."""
        self.request = Rtsp.parseRequest(message)

        if self.request["method"] == Rtsp.Method.SETUP:
            self.setup()

        if self.request["method"] == Rtsp.Method.PLAY:
            self.play()

        if self.request["method"] == Rtsp.Method.PAUSE:
            self.pause()

        if self.request["method"] == Rtsp.Method.TEARDOWN:
            self.teardown()


    def _setup_(self) -> bool:
        try:
            self.videoReader = VideoReader(self.request["fileName"])
            self.state = self.READY
        except IOError:
            self.sendRtspRespond(Rtsp.StatusCode.FILE_NOT_FOUND)
            return False

        self.session = randint(100000, 999999)
        self.clientRtpPort = self.request["clientPort"]
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtpSocket.connect((self.clientIp, self.clientRtpPort))

        self.sendRtspRespond(Rtsp.StatusCode.OK, isSetup=True)
        return True

    def _play_(self) -> bool:
        self.sendRtspRespond(Rtsp.StatusCode.OK)
        return True

    def _pause_(self) -> bool:
        self.sendRtspRespond(Rtsp.StatusCode.OK)
        return True

    def _teardown_(self) -> bool:
        self.rtpSocket.close()
        self.sendRtspRespond(Rtsp.StatusCode.OK)
        return True


    def _stream_(self) -> None:
        ok, frame = self.videoReader.nextFrame()
        if not ok:
            return

        binFrame = pickle.dumps(frame)
        data = {
            "version": 2,
            # "padding": 0, # does not support padding, defaults to 0
            # "extension": 0, # does not support extension, defaults to 0
            # "csrcCount": 0, # does not support other than 0
            # "marker": 0,
            "payloadType": 26, # MJPEG type
            "timestamp": self.frameCounter.getThenIncrement(),
            "ssrc": 123,
            # "csrcList": [], # does not support other than empty list
            # "sequenceNumber": self.rtpSequenceNumber.getThenIncrement(),
            # "payload": pickle.dumps(fitPayload(frame))
        }

        sz = Rtp.PAYLOAD_SIZE
        i = 0
        while i < len(binFrame):
            j = min(i + sz, len(binFrame))
            data["payload"] = binFrame[i:j]
            data["sequenceNumber"] = self.rtpSequenceNumber.getThenIncrement()
            data["marker"] = (j == len(binFrame))
            p = Rtp.Packet(data)
            # print(p)
            self.rtpSocket.sendall(p.encode())

            i = j



    def run(self) -> None:
        while True:
            message = self.rtspSocket.recv(Rtsp.RTSP_MESSAGE_SIZE)
            if not message:
                break
            self.processRtspRequest(message.decode())

        self.teardown()
        self.rtspSocket.close()

