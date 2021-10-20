from random import randint
import socket
from cv2 import VideoCapture

from common import *
from MediaPlayer import MediaPlayer
import Rtsp
from RtpPacket import RtpPacket

class ServerWorker(MediaPlayer):
    def __init__(self, rtspSocket: socket.socket, clientIp: str, clientRtspPort: int) -> None:
        super().__init__()

        self.rtspSocket = rtspSocket
        self.clientIp = clientIp
        self.clientRtspPort = clientRtspPort

        self.session = 0

        self.videoReader: VideoCapture = None
        self.clientRtpPort = 0

        self.rtpSocket = None

        self.request = None

    def __del__(self) -> None:
        self.teardown()
        self.rtspSocket.close()

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
            self.videoReader = VideoCapture(self.request["fileName"])
            self.state = self.READY
        except IOError:
            self.sendRtspRespond(Rtsp.StatusCode.FILE_NOT_FOUND)
            return False

        self.session = randint(100000, 999999)
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.clientRtpPort = self.request["clientPort"]

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
        self.videoReader.release()
        self.sendRtspRespond(Rtsp.StatusCode.OK)
        return True

    def processFrame(self) -> None:
        ok, frame = self.videoReader.read()
        client = (self.clientIp, self.clientRtpPort)

        data = frame.tobytes()
        sz = RTP_BUFFER_SIZE
        for i in range(0, len(data), sz):
            j = min(i + sz, len(data))
            data[i:j]
            self.rtpSocket.sendto(data[i:j], client)

    def makeRtp(self, payload, frameNbr):
        """RTP-packetize the video data."""
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26 # MJPEG type
        seqnum = frameNbr
        ssrc = 0

        rtpPacket = RtpPacket()

        rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)

        return rtpPacket.getPacket()

    def run(self) -> None:
        while True:
            message = self.rtspSocket.recv(RTSP_BUFFER_SIZE)
            if not message:
                break
            self.processRtspRequest(message.decode())
