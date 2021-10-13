from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket
import RtspProcessor

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT
    
    def __init__(self, serverAddr, rtspPort, rtpPort, fileName):
        self.serverAddr = serverAddr
        self.rtspPort = rtspPort
        self.rtpPort = rtpPort
        self.fileName = fileName

        self.connectToServer()
        self.createWidgets()

        self.frameNbr = 0


    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        # the owner of the rtsp socket is the processor even though 
        # the socket is created outside the processor
        rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        rtspSocket.connect((self.serverAddr, self.rtspPort))
        self.rtspProcessor = RtspProcessor.Client(rtspSocket, self.rtpPort, self.fileName)

    def createWidgets(self):
        """Build GUI."""
        self.master = Tk()
        self.master.title('Client')

        # Create Setup button
        self.setup = Button(self.master, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=1, column=0, padx=2, pady=2)
        
        # Create Play button		
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)
        
        # Create Pause button			
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=1, column=2, padx=2, pady=2)
        
        # Create Teardown button
        self.teardown = Button(self.master, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] =  self.exitClient
        self.teardown.grid(row=1, column=3, padx=2, pady=2)
        
        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 

        # self.master.protocol("WM_DELETE_WINDOW", self.GUICloseHandler)

    def __del__(self):
        print("client destroyed")
        
    def setupMovie(self):
        self.rtspProcessor.sendRequest(RtspProcessor.Method.SETUP)

    def exitClient(self):
        self.rtspProcessor.sendRequest(RtspProcessor.Method.TEARDOWN)

    def pauseMovie(self):
        self.rtspProcessor.sendRequest(RtspProcessor.Method.PAUSE)
    
    def playMovie(self):
        self.rtspProcessor.sendRequest(RtspProcessor.Method.PLAY)
    
    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        #TODO
    
    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        #TODO

        
    def run(self):
        self.master.mainloop()

if __name__ == "__main__":
    try:
        serverAddr = sys.argv[1]
        rtspPort = int(sys.argv[2])
        rtpPort = int(sys.argv[3])
        fileName = sys.argv[4]	
    except:
        print("Usage: ClientLauncher.py Server_name Server_port RTP_port Video_file\n")	
    
    
    # Create a new client
    app = Client(serverAddr, rtspPort, rtpPort, fileName)
    app.run()
    