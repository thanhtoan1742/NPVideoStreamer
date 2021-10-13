from enum import Enum
from random import randint
import socket

class Method:
    SETUP = "SETUP"
    PLAY = "PLAY"
    PAUSE = "PAUSE"
    TEARDOWN = "TEARDOWN "

class StatusCode:
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
        """
        the socket will be closed when this instance get destroyed.
        """
        self.socket = socket
        self.rtpPort = rtpPort
        self.fileName = fileName 

        self.CSeq = 0
        self.session = 0

    def __del__(self):
        self.socket.close()

    def createRequest(self, method: Method) -> str:
        self.CSeq += 1

        request = f"{method} {self.fileName} RTSP/1.0\n"
        request += f"CSeq: {self.CSeq}\n"
        if method == Method.SETUP:
            self.session = randint(100000, 999999)
            request += f"Transport: RTP/UDP; client_port={self.rtpPort}\n"
        else:
            assert self.session != 0
            request += f"Session: {self.session}\n"

        return request

    def createRespond(self, statusCode: StatusCode, CSeq: int) -> str:
        respond = f"RTSP/1.0 {statusCode} {StatusCode.DESCRIPTION[statusCode]}"
        assert CSeq != 0
        respond += f"CSeq: {self.CSeq}\n"
        assert self.session != 0
        respond += f"Session: {self.session}\n"

        return respond

    def sendMessage(self, message: str) -> None:
        print("\nsend\n", message, sep="")
        self.socket.sendall(message.encode())

    def receiveMessage(self) -> str:
        message = self.socket.recv(1024)
        print("\nreceive\n", str(message), sep="")
        return str(message)

    def sendRequest(self, method: Method) -> None:
        message = self.createRequest(method)
        self.sendMessage(message)

    def sendRespond(self, statusCode: StatusCode, CSeq: int) -> None:
        message = self.createRespond(statusCode, CSeq)
        self.sendMessage(message)

    def parseRequest(self, message: str) -> dict:
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

    def parseRespond(self, message: str) -> dict:
        respond = {}

        lines = message.split('\n')
        line = lines[0].split()
        respond["statusCode"] = int(line[1])

        line = lines[1].split(":")
        respond["CSeq"] = int(line[1])

        line = lines[2].split(":")
        respond["session"] = int(line[1])

        return respond