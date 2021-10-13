from enum import Enum
from random import randint
import socket

def log(message: str, header: str = ""):
    print("-"*40)
    print(header)
    print(message)
    print("-"*40)

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
    only allows play 1 file on 1 RTP port over 1 session.
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

    def sendMessage(self, message: str) -> None:
        self.socket.sendall(message.encode())

    def receiveMessage(self) -> str:
        message = self.socket.recv(1024)
        return message.decode()





class Client(Processor):
    def __init__(self, socket: socket.socket, rtpPort: int, fileName: str) -> None:
        super().__init__(socket, rtpPort, fileName)

    def createRequestMessage(self, method: Method) -> str:
        self.CSeq += 1

        message = f"{method} {self.fileName} RTSP/1.0\n"
        message += f"CSeq: {self.CSeq}\n"
        if method == Method.SETUP:
            message += f"Transport: RTP/UDP; client_port={self.rtpPort}\n"
        else:
            assert self.session != 0
            message += f"Session: {self.session}\n"

        return message

    def sendRequest(self, method: Method) -> dict:
        message = self.createRequestMessage(method)
        self.sendMessage(message)

        respond = self.receiveRespond()
        self.session = respond["session"]

        return respond

    def parseRespond(self, message: str) -> dict:
        log(message, "parse respond")
        respond = {}

        lines = message.split('\n')
        line = lines[0].split()
        respond["statusCode"] = int(line[1])

        line = lines[1].split(":")
        respond["CSeq"] = int(line[1])

        line = lines[2].split(":")
        respond["session"] = int(line[1])

        return respond

    def receiveRespond(self) -> dict:
        message = self.receiveMessage()
        return self.parseRespond(message)




class Server(Processor):
    def __init__(self, socket: socket.socket, rtpPort: int, fileName: str) -> None:
        super().__init__(socket, rtpPort, fileName)

    def createRespondMessage(self, statusCode: StatusCode, CSeq: int) -> str:
        message = f"RTSP/1.0 {statusCode} {StatusCode.DESCRIPTION[statusCode]}"
        assert CSeq != 0
        message += f"CSeq: {self.CSeq}\n"
        assert self.session != 0
        message += f"Session: {self.session}\n"

        return message

    def sendRespond(self, statusCode: StatusCode, CSeq: int) -> None:
        message = self.createRespondMessage(statusCode, CSeq)
        self.sendMessage(message)

    def parseRequest(self, message: str) -> dict:
        log(message, "parse request")
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

    def receiveRequest(self) -> dict:
        message = self.receiveMessage()
        request = self.parseRequest(message)

        if request["method"] == Method.SETUP:
            self.session = randint(100000, 999999)
        self.CSeq = request["CSeq"]

        return request