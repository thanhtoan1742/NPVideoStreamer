import sys, socket
from tkinter.constants import W
from RtpPacket import RtpPacket
from threading import Thread

from common import *
from ServerWorker import ServerWorker

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


if __name__ == "__main__":
    try:
        rtspPort = int(sys.argv[1])
    except:
        print("Usage: python Server.py rtspPort\n")

    app = Server("", rtspPort)
    app.run()


