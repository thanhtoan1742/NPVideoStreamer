import pickle
import socket
from random import randint

from npvs import ps
from npvs import rtp
from npvs import rtsp
from npvs.atomic_counter import AtomicCounter
from npvs.common import *
from npvs.media_player import MediaPlayer
from npvs.video import VideoReader


class ServerWorker(MediaPlayer):
    def __init__(
        self, rtspSocket: socket.socket, clientIp: str, clientRtspPort: int
    ) -> None:
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

        self.logger = get_logger("server-worker")

    def __del__(self) -> None:
        pass

    def send_RTSP_respond(
        self, statusCode: rtsp.StatusCode, isSetup: bool = False
    ) -> None:
        """Send rtsp reply to the client."""
        respond = {"statusCode": statusCode, "CSeq": self.request["CSeq"]}
        if statusCode == rtsp.StatusCode.OK:
            respond["session"] = self.session
        message = rtsp.create_response(respond)

        self.rtspSocket.send(message.encode())

    def process_RTSP_request(self, message: str) -> None:
        """Process rtsp request sent from the client."""
        self.request = rtsp.parse_request(message)

        if self.request["method"] == rtsp.Method.SETUP:
            self.setup()

        if self.request["method"] == rtsp.Method.PLAY:
            self.play()

        if self.request["method"] == rtsp.Method.PAUSE:
            self.pause()

        if self.request["method"] == rtsp.Method.TEARDOWN:
            self.teardown()

    def _setup_(self) -> bool:
        try:
            self.videoReader = VideoReader(self.request["fileName"])
            self.state = self.READY
        except IOError:
            self.send_RTSP_respond(rtsp.StatusCode.FILE_NOT_FOUND)
            return False

        self.session = randint(100000, 999999)
        self.clientRtpPort = self.request["clientPort"]
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtpSocket.connect((self.clientIp, self.clientRtpPort))

        self.send_RTSP_respond(rtsp.StatusCode.OK, isSetup=True)
        return True

    def _play_(self) -> bool:
        self.send_RTSP_respond(rtsp.StatusCode.OK)
        return True

    def _pause_(self) -> bool:
        self.send_RTSP_respond(rtsp.StatusCode.OK)
        return True

    def _teardown_(self) -> bool:
        self.rtpSocket.close()
        self.send_RTSP_respond(rtsp.StatusCode.OK)
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
            "payloadType": 26,  # MJPEG type
            "timestamp": self.frameCounter.get_then_increment(),
            "ssrc": 123,
            # "csrcList": [], # does not support other than empty list
            # "sequenceNumber": self.rtpSequenceNumber.getThenIncrement(),
            # "payload": pickle.dumps(fitPayload(frame))
        }

        sz = rtp.PAYLOAD_SIZE
        i = 0
        while i < len(binFrame):
            j = min(i + sz, len(binFrame))
            data["payload"] = binFrame[i:j]
            data["sequenceNumber"] = self.rtpSequenceNumber.get_then_increment()
            data["marker"] = j == len(binFrame)
            rtpPacket = rtp.packet_from_dict(data)
            p = ps.Packet(rtpPacket.encode())
            self.rtpSocket.sendall(p.encode())
            self.logger.info(
                "sent packet size: %s, packet: ", str(p.payload_size()), str(rtpPacket)
            )

            i = j

    def run(self) -> None:
        while True:
            message = self.rtspSocket.recv(rtsp.RTSP_MESSAGE_SIZE)
            if not message:
                break
            self.process_RTSP_request(message.decode())

        self.teardown()
        self.rtspSocket.close()
