from enum import Enum
import socket

class Method(Enum):
    SETUP = "SETUP"
    PLAY = "PLAY"
    PAUSE = "PAUSE"
    TEARDOWN = "TEARDOWN "

class StatusCode(Enum):
    OK = 200
    FILE_NOT_FOUND = 404
    CONNECTION_ERROR = 500

    DESCRIPTION = {
        OK: "OK",
        FILE_NOT_FOUND: "FILE_NOT_FOUND",
        CONNECTION_ERROR: "CONNECTION_ERROR" 
    }

class Processor:
    """
    RTSP processor
    only allows play 1 file on 1 RTP port.
    """
    def __init__(self, socket: socket.socket, rtpPort: int, fileName: str) -> None:
        self.socket = socket
        self.rtpPort = rtpPort
        self.fileName = fileName 

        self.CSeq = 0
        self.session = 0

    def createRtspRequest(self, method: Method) -> str:
        self.CSeq += 1

        request = f"{method} {self.fileName} RTSP/1.0\n"
        request += f"CSeq: {self.CSeq}\n"
        if method == Method.SETUP:
            request += f"Transport: RTP/UDP; client_port=\n"
        else:
            assert self.session != 0
            request += f"Session: {self.session}\n"

        return request

    def createRtspRespond(self, statusCode: StatusCode, CSeq: int) -> str:
        respond = f"RTSP/1.0 {statusCode} {StatusCode.DESCRIPTION[statusCode]}"
        assert CSeq != 0
        respond += f"CSeq: {self.CSeq}\n"
        assert self.session != 0
        respond += f"Session: {self.session}\n"

        return respond

    def sendRtspMessage(self, message: str) -> None:
        self.socket.sendall(message.encode())

    def receiveRtspMessage(self) -> str:
        message = self.socket.recv(1024)
        return str(message)

    def sendRtspRequest(self, method: Method) -> None:
        message = self.createRtspRequest(method)
        self.sendRtspMessage(message)

    def sendRtspRespond(self, statusCode: StatusCode, CSeq: int) -> None:
        message = self.createRtspRespond(statusCode, CSeq)
        self.sendRtspMessage(message)

    def parseRtspRequest(self, message: str) -> dict:
        request = {}

        lines = message.split('\n')
        line = lines[0].split()
        request["method"] = line[0]
        request["fileName"] = line[1]

        line = lines[1].split(":")
        request["CSeq"] = int(line[1])

        line = lines[2].split(":")
        request["session"] = int(line[1])

        return request

    def parseRtspRespond(self, message: str) -> dict:
        respond = {}

        lines = message.split('\n')
        line = lines[0].split()
        respond["statusCode"] = int(line[1])

        line = lines[1].split(":")
        respond["CSeq"] = int(line[1])

        line = lines[2].split(":")
        respond["session"] = int(line[1])

        return respond