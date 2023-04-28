import json
import pickle
import socket
from random import randint


from npvs import ps, rtp, rtsp
from npvs.common import *
from npvs.dumper import Dumper
from npvs.media_player import MediaPlayer
from npvs.ps_receiver import PsReceiver
from npvs.video import VideoReader


class ServerWorker(MediaPlayer):
    def __init__(
        self, rtsp_socket: socket.socket, client_ip: str, client_rtsp_port: int
    ) -> None:
        super().__init__()
        self.logger = get_logger("server-worker")
        self.logger.info(
            "server worker created, serving (%s, %s)", client_ip, client_rtsp_port
        )

        self.rtsp_socket = rtsp_socket
        self.client_ip = client_ip
        self.client_rtsp_port = client_rtsp_port
        self.rtsp_session = 0
        self.request = None

        self.rtp_socket: socket.socket = None
        self.client_rtp_port = 0
        self.rtp_sequence_number = 0

        self.video_reader: VideoReader = None

        # self.dumper = Dumper("server-data.bin")

    def __del__(self) -> None:
        self.rtsp_socket.close()

    def send_RTSP_response(self, status_code: rtsp.StatusCode) -> None:
        """Send RTSP response to the client."""
        response = {"statusCode": status_code, "CSeq": self.request["CSeq"]}
        if status_code == rtsp.StatusCode.OK:
            response["session"] = self.rtsp_session
        message = rtsp.create_response(response)

        self.rtsp_socket.send(message.encode())
        self.logger.info("sent RTPS message = %s", json.dumps(response, indent=2))

    def process_RTSP_request(self, message: str) -> None:
        """Process rtsp request sent from the client."""
        self.request = rtsp.parse_request(message)
        self.logger.info(
            "processing RTSP message = %s", json.dumps(self.request, indent=2)
        )

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
            self.video_reader = VideoReader(self.request["fileName"])
            self.state = self.READY
        except IOError:
            self.send_RTSP_response(rtsp.StatusCode.FILE_NOT_FOUND)
            return False
        self.logger.info("video reader reading file %s", self.request["fileName"])

        self.rtsp_session = randint(100000, 999999)
        self.client_rtp_port = self.request["clientPort"]
        self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtp_socket.connect((self.client_ip, self.client_rtp_port))
        self.logger.info(
            "RTP socket opened, serving (%s, %s)", self.client_ip, self.client_rtp_port
        )

        self.send_RTSP_response(rtsp.StatusCode.OK)
        return True

    def _play_(self) -> bool:
        self.send_RTSP_response(rtsp.StatusCode.OK)
        return True

    def _pause_(self) -> bool:
        self.send_RTSP_response(rtsp.StatusCode.OK)
        return True

    def _teardown_(self) -> bool:
        self.rtp_socket.close()
        self.send_RTSP_response(rtsp.StatusCode.OK)
        self.logger.info(
            "RTP socket closed, stop serving (%s, %s)",
            self.client_ip,
            self.client_rtp_port,
        )
        return True

    def _stream_(self) -> None:
        ok, frame = self.video_reader.next_frame()
        if not ok:
            return

        bin_frame = pickle.dumps(frame)
        data = {
            "version": 2,
            # "padding": 0, # does not support padding, defaults to 0
            # "extension": 0, # does not support extension, defaults to 0
            # "csrcCount": 0, # does not support other than 0
            # "marker": 0,
            "payloadType": 26,  # MJPEG type
            "timestamp": self.video_reader.frame_counter - 1,
            "ssrc": 123,
            # "csrcList": [], # does not support other than empty list
            # "sequenceNumber": self.rtpSequenceNumber.getThenIncrement(),
            # "payload": pickle.dumps(fitPayload(frame))
        }

        i = 0
        while i < len(bin_frame):
            j = min(i + rtp.PAYLOAD_SIZE, len(bin_frame))

            data["payload"] = bin_frame[i:j]
            data["marker"] = j == len(bin_frame)
            data["sequenceNumber"] = self.rtp_sequence_number
            self.rtp_sequence_number += 1

            packet = ps.Packet(rtp.packet_from_dict(data).encode())

            try:
                self.rtp_socket.sendall(packet.encode())
            except Exception as e:
                self.logger.error("Expcetion when try to send RTP data, e = %s", str(e))
                raise e

            self.logger.debug(
                "sent ps packet with payload size: %s", str(packet.payload_size())
            )
            # self.dumper.append(packet.encode())

            i = j

    def run(self) -> None:
        while True:
            message = self.rtsp_socket.recv(rtsp.RTSP_MESSAGE_SIZE)
            if not message:
                break
            self.process_RTSP_request(message.decode())

        self.teardown()
