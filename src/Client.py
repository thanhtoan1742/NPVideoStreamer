import tkinter as tk
from PIL import ImageTk
import socket, sys
import pickle
import time

from numpy.lib.type_check import imag

from common import *
from MediaPlayer import MediaPlayer
from VideoAssembler import RtpVideoAssembler
import Rtsp, Rtp


class Client(MediaPlayer):
    def __init__(self, serverIp: str, serverRtspPort: int, fileName: str) -> None:
        super().__init__()

        self.serverIp = serverIp
        self.serverRtspPort = serverRtspPort
        self.fileName = fileName

        self.clientRtpPort = 0
        self.rtpSocket = None

        # self.videoAssembler = RtpVideoAssembler()

        self.initRtsp()
        self.initGUI()


    def initRtsp(self) -> None:
        """Connect to the Server. Start a new RTSP/TCP session."""

        self.CSeq = 0
        self.session = -1

        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtspSocket.connect((self.serverIp, self.serverRtspPort))

    def initGUI(self) -> None:
        """Build GUI."""
        self.guiRoot = tk.Tk()
        self.guiRoot.title('Client')

        # Create Setup button
        self.setupButton = tk.Button(self.guiRoot, width=20, padx=3, pady=3)
        self.setupButton["text"] = "Setup"
        self.setupButton["command"] = self.setup
        self.setupButton.grid(row=1, column=0, padx=2, pady=2)

        # Create Play button
        self.playButton = tk.Button(self.guiRoot, width=20, padx=3, pady=3)
        self.playButton["text"] = "Play"
        self.playButton["command"] = self.play
        self.playButton.grid(row=1, column=1, padx=2, pady=2)

        # Create Pause button
        self.pauseButton = tk.Button(self.guiRoot, width=20, padx=3, pady=3)
        self.pauseButton["text"] = "Pause"
        self.pauseButton["command"] = self.pause
        self.pauseButton.grid(row=1, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardownButton = tk.Button(self.guiRoot, width=20, padx=3, pady=3)
        self.teardownButton["text"] = "Teardown"
        self.teardownButton["command"] =  self.teardown
        self.teardownButton.grid(row=1, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = tk.Label(self.guiRoot)
        self.label.grid(row=0, column=0, columnspan=4, sticky=tk.W+tk.E+tk.N+tk.S, padx=5, pady=5)

        # self.master.protocol("WM_DELETE_WINDOW", self.GUICloseHandler)

    def __del__(self) -> None:
        self.teardown()

    def sendRtspRequest(self, method: Rtsp.Method) -> bool:
        self.CSeq += 1

        request = {
            "method": method,
            "fileName": self.fileName,
            "CSeq": self.CSeq,
        }
        if method == Rtsp.Method.SETUP:
            request["clientPort"] = self.clientRtpPort
        else:
            request["session"] = self.session
        message = Rtsp.createRequest(request)
        self.rtspSocket.sendall(message.encode())

        message = self.rtspSocket.recv(SOCKET_BUFFER_SIZE).decode()
        self.respond = Rtsp.parseRespond(message)
        if self.respond["statusCode"] > 299:
            log(self.respond["statusCode"], "server responded")
            return False

        return True


    def _setup_(self) -> bool:
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpSocket.bind(("", 0)) # let os pick port
        self.clientRtpPort  = int(self.rtpSocket.getsockname()[1]) # get the port

        if not self.sendRtspRequest(Rtsp.Method.SETUP):
            return False

        self.session = self.respond["session"]
        return True

    def _play_(self) -> bool:
        return self.sendRtspRequest(Rtsp.Method.PLAY)

    def _pause_(self) -> bool:
        return self.sendRtspRequest(Rtsp.Method.PAUSE)

    def _teardown_(self) -> bool:
        if not self.sendRtspRequest(Rtsp.Method.TEARDOWN):
            return False
        self.rtpSocket.close()
        return True


    def processFrame(self) -> None:
        data, host = self.rtpSocket.recvfrom(SOCKET_BUFFER_SIZE)
        data = Rtp.decode(data)

        frame = pickle.loads(data["payload"])
        self.frameTk = ImageTk.PhotoImage(image=frame)
        self.label.configure(image=self.frameTk)
        time.sleep(1/30)


    def run(self) -> None:
        self.guiRoot.mainloop()


if __name__ == "__main__":
    try:
        serverIp = sys.argv[1]
        rtspPort = int(sys.argv[2])
        fileName = sys.argv[3]
    except:
        print("Usage: python Client.py serverIP serverRtspPort fileName\n")

    # Create a new client
    app = Client(serverIp, rtspPort, fileName)
    app.run()
