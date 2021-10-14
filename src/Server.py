import sys, socket
from tkinter.constants import W
from RtpPacket import RtpPacket
from threading import Thread

from ServerWorker import ServerWorker

class Server:
    def __init__(self, Ip, rtspPort) -> None:
        self.Ip = Ip
        self.rtspPort = rtspPort

    def run(self):
        rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rtspSocket.bind((self.Ip, self.rtspPort))
        rtspSocket.listen(5)


        # Receive client info (address,port) through RTSP/TCP session
        while True:
            clientInfo = {}
            clientInfo['rtspSocket'] = rtspSocket.accept()
            sw = ServerWorker(clientInfo)
            Thread(target=sw.run).start()


if __name__ == "__main__":
    try:
        rtspPort = int(sys.argv[1])
    except:
        print("Usage: python Server.py rtspPort\n")

    app = Server("", rtspPort)
    app.run()


