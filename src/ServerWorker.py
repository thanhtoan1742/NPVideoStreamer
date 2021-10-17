from random import randint
import threading, socket

from common import *
from MediaPlayer import MediaPlayer
import Rtsp
from RtpPacket import RtpPacket
from VideoReader import VideoReader

class ServerWorker(MediaPlayer):
    def __init__(self, rtspSocket: socket.socket, clientIp: str, clientRtspPort: int) -> None:
        super().__init__()

        self.rtspSocket = rtspSocket
        self.clientIp = clientIp
        self.clientRtspPort = clientRtspPort

        self.session = 0

        self.videoStream = None
        self.rtpPort = 0
        self.rtpSocket = None
        # self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.request = None

    def __del__(self) -> None:
        if self.rtpSocket != None:
            self.rtpSocket.close()
        self.rtspSocket.close()

    def sendRtspRespond(self, statusCode: Rtsp.StatusCode) -> None:
        """Send RTSP reply to the client."""
        if statusCode == Rtsp.StatusCode.OK:
            message = Rtsp.createRespond(statusCode, self.request["CSeq"], self.session)
        else:
            message = Rtsp.createRespond(statusCode, self.request["CSeq"])
        self.rtspSocket.send(message.encode())
        log(message, "server sent")

    def processRtspRequest(self, message: str) -> None:
        """Process RTSP request sent from the client."""
        log(message, "server received")
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
            self.videoStream = VideoReader(self.request["fileName"])
            self.state = self.READY
        except IOError:
            self.sendRtspRespond(Rtsp.StatusCode.FILE_NOT_FOUND)
            return False

        self.session = randint(100000, 999999)
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpPort = self.request["rtpPort"]
        self.sendRtspRespond(Rtsp.StatusCode.OK)
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

    def processFrame(self) -> None:
        print("processed frame")

    def sendRtp(self) -> None:
        """Send RTP packets over UDP."""
        while True:
            self.playingFlag.wait(0.05)

            # Stop sending if request is PAUSE or TEARDOWN
            if self.playingFlag.is_set():
                break

            data = self.videoStream.nextFrame()
            if data:
                frameNumber = self.videoStream.frameNbr()
                try:
                    address = self.clientIp
                    port = self.rtpPort
                    self.rtpSocket.sendto(self.makeRtp(data, frameNumber),(address,port))
                except:
                    print("Connection Error")
                    #print('-'*60)
                    #traceback.print_exc(file=sys.stdout)
                    #print('-'*60)

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
            message = self.rtspSocket.recv(1024)
            if not message:
                break
            self.processRtspRequest(message.decode())