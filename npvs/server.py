import socket
from threading import Thread

from npvs.common import *
from npvs.server_worker import ServerWorker


class Server:
    def __init__(self, Ip, rtspPort) -> None:
        self.Ip = Ip
        self.rtspPort = rtspPort

        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtspSocket.bind((self.Ip, self.rtspPort))
        self.rtspSocket.listen(5)

    def __del__(self) -> None:
        self.rtspSocket.close()

    def run(self):
        # Receive client info (address,port) through RTSP/TCP session
        workers = []
        while True:
            clientSocket, (clientIp, clientPort) = self.rtspSocket.accept()

            worker = ServerWorker(clientSocket, clientIp, clientPort)
            workers.append(worker)
            Thread(target=worker.run).start()
