from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from common import *
from RtpPacket import RtpPacket
from Player import Player
import Rtsp

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client(Player):
    def __init__(self, serverIp: str, rtspPort: int, rtpPort: int, fileName: str) -> None:
        super().__init__()

        self.serverIp = serverIp
        self.rtspPort = rtspPort
        self.rtpPort = rtpPort
        self.fileName = fileName

        self.initRtsp()
        self.initGUI()

    def initRtsp(self) -> None:
        """Connect to the Server. Start a new RTSP/TCP session."""

        self.CSeq = 0
        self.session = -1

        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtspSocket.connect((self.serverIp, self.rtspPort))

    def initGUI(self) -> None:
        """Build GUI."""
        self.guiRoot = Tk()
        self.guiRoot.title('Client')

        # Create Setup button
        self.setupButton = Button(self.guiRoot, width=20, padx=3, pady=3)
        self.setupButton["text"] = "Setup"
        self.setupButton["command"] = self.setup
        self.setupButton.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.playButton = Button(self.guiRoot, width=20, padx=3, pady=3)
        self.playButton["text"] = "Play"
        self.playButton["command"] = self.play
        self.playButton.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pauseButton = Button(self.guiRoot, width=20, padx=3, pady=3)
        self.pauseButton["text"] = "Pause"
        self.pauseButton["command"] = self.pause
        self.pauseButton.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardownButton = Button(self.guiRoot, width=20, padx=3, pady=3)
        self.teardownButton["text"] = "Teardown"
        self.teardownButton["command"] =  self.teardown
        self.teardownButton.grid(row=1, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.guiRoot, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5)

        # self.master.protocol("WM_DELETE_WINDOW", self.GUICloseHandler)

    def __del__(self) -> None:
        print("client destroyed")

    def sendRtspRequest(self, method: Rtsp.Method) -> bool:
        self.CSeq += 1
        if method == Rtsp.Method.SETUP:
            message = Rtsp.createRequest(Rtsp.Method.SETUP, self.CSeq, self.fileName, rtpPort=self.rtpPort)
        else:
            message = Rtsp.createRequest(method, self.CSeq, self.fileName, session=self.session)
        log(message, "client send")
        self.rtspSocket.sendall(message.encode())

        message = self.rtspSocket.recv(1024).decode()
        log(message, "client receive")
        respond = Rtsp.parseRespond(message)
        if respond["statusCode"] > 299:
            print(respond["statusCode"])
            return False

        if method == Rtsp.Method.SETUP:
            self.session = respond["session"]

        return True


    def _setup_(self) -> bool:
        return self.sendRtspRequest(Rtsp.Method.SETUP)

    def _play_(self) -> bool:
        return self.sendRtspRequest(Rtsp.Method.PLAY)

    def _pause_(self) -> bool:
        return self.sendRtspRequest(Rtsp.Method.PAUSE)

    def _teardown_(self) -> bool:
        return self.sendRtspRequest(Rtsp.Method.TEARDOWN)

    def run(self) -> None:
        self.guiRoot.mainloop()

if __name__ == "__main__":
    try:
        serverIp = sys.argv[1]
        rtspPort = int(sys.argv[2])
        rtpPort = int(sys.argv[3])
        fileName = sys.argv[4]
    except:
        print("Usage: python Client.py serverIP serverRtspPort clientRtpPort fileName\n")


    # Create a new client
    app = Client(serverIp, rtspPort, rtpPort, fileName)
    app.run()