from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	
	def __init__(self, serverAddr, serverPort, rtpPort, fileName):
		self.serverAddr = serverAddr
		self.serverPort = serverPort
		self.rtpPort = rtpPort
		self.fileName = fileName

		self.connectToServer()
		self.createWidgets()

	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.frameNbr = 0

		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.rtspSocket.connect((self.serverAddr, self.serverPort))
		self.rtspSocket.sendall(b'ping')
		message = self.rtspSocket.recv(16)
		print(message)



	def __del__(self):
		self.rtspSocket.close()
		print("client destroyed")
		
	# Initiatio
	# THIS GUI IS JUST FOR REFERENCE ONLY, STUDENTS HAVE TO CREATE THEIR OWN GUI 	
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

	
	def setupMovie(self):
		"""Setup button handler."""
	#TODO
	
	def exitClient(self):
		"""Teardown button handler."""
	#TODO

	def pauseMovie(self):
		"""Pause button handler."""
	#TODO
	
	def playMovie(self):
		"""Play button handler."""
	#TODO
	
	def listenRtp(self):		
		"""Listen for RTP packets."""
		#TODO
					
	def writeFrame(self, data):
		"""Write the received frame to a temp image file. Return the image file."""
	#TODO
	
	def updateMovie(self, imageFile):
		"""Update the image file as video frame in the GUI."""
	#TODO
		
	
	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""	
		#-------------
		# TO COMPLETE
		#-------------
		
	
	
	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		#TODO
	
	def parseRtspReply(self, data):
		"""Parse the RTSP reply from the server."""
		#TODO
	
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		#-------------
		# TO COMPLETE
		#-------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		
		# Set the timeout value of the socket to 0.5sec
		# ...
		
	def run(self):
		self.master.mainloop()

if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = int(sys.argv[2])
		rtpPort = int(sys.argv[3])
		fileName = sys.argv[4]	
	except:
		print("Usage: ClientLauncher.py Server_name Server_port RTP_port Video_file\n")	
	
	
	# Create a new client
	app = Client(serverAddr, serverPort, rtpPort, fileName)
	app.run()
	