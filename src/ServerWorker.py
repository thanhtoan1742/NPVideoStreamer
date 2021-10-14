from os import pipe
from random import randint
import sys, traceback, threading, socket
from tkinter import Frame

from common import *
from VideoStream import VideoStream
from RtpPacket import RtpPacket
import Rtsp

class ServerWorker:
    SETUP = 'SETUP'
    PLAY = 'PLAY'
    PAUSE = 'PAUSE'
    TEARDOWN = 'TEARDOWN'

    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    OK_200 = 0
    FILE_NOT_FOUND_404 = 1
    CON_ERR_500 = 2

    clientInfo = {}

    def __init__(self, clientInfo):
        self.clientInfo = clientInfo

    def recvRtspRequest(self):
        """Receive RTSP request from the client."""
        connSocket = self.clientInfo['rtspSocket'][0]
        while True:
            message = connSocket.recv(1024)
            if message:
                self.processRtspRequest(message.decode())

    def processRtspRequest(self, data):
        """Process RTSP request sent from the client."""
        request = Rtsp.parseRequest(data)

        # Process SETUP request
        if request["method"] == self.SETUP:
            if self.state == self.INIT:
                # Update state
                print("processing SETUP\n")

                try:
                    self.clientInfo['videoStream'] = VideoStream(request["fileName"])
                    self.state = self.READY
                except IOError:
                    self.replyRtsp(self.FILE_NOT_FOUND_404, request["CSeq"])
                    return

                # Generate a randomized RTSP session ID
                self.clientInfo["session"] = randint(100000, 999999)

                # Send RTSP reply
                self.replyRtsp(self.OK_200, request["CSeq"])

                # Get the RTP/UDP port from the last line
                self.clientInfo['rtpPort'] = request["rtpPort"]

        # Process PLAY request
        elif request["method"] == self.PLAY:
            if self.state == self.READY:
                print("processing PLAY\n")
                self.state = self.PLAYING

                # Create a new socket for RTP/UDP
                self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                self.replyRtsp(self.OK_200, request["CSeq"])

                # Create a new thread and start sending RTP packets
                self.clientInfo['event'] = threading.Event()
                self.clientInfo['worker']= threading.Thread(target=self.sendRtp)
                self.clientInfo['worker'].start()

        # Process PAUSE request
        elif request["method"] == self.PAUSE:
            if self.state == self.PLAYING:
                print("processing PAUSE\n")
                self.state = self.READY

                self.clientInfo['event'].set()

                self.replyRtsp(self.OK_200, request["CSeq"])

        # Process TEARDOWN request
        elif request["method"] == self.TEARDOWN:
            print("processing TEARDOWN\n")

            self.clientInfo['event'].set()

            self.replyRtsp(self.OK_200, request["CSeq"])

            # Close the RTP socket
            self.clientInfo['rtpSocket'].close()

    def sendRtp(self):
        """Send RTP packets over UDP."""
        while True:
            self.clientInfo['event'].wait(0.05)

            # Stop sending if request is PAUSE or TEARDOWN
            if self.clientInfo['event'].isSet():
                break

            data = self.clientInfo['videoStream'].nextFrame()
            if data:
                frameNumber = self.clientInfo['videoStream'].frameNbr()
                try:
                    address = self.clientInfo['rtspSocket'][1][0]
                    port = int(self.clientInfo['rtpPort'])
                    self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber),(address,port))
                except:
                    print("Connection Error")
                    #print('-'*60)
                    #traceback.print_exc(file=sys.stdout)
                    #print('-'*60)

    def makeRtp(self, payload, frameNbr):
        """RTP-packetize the video data."""
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26 # MJPEG type
        seqnum = frameNbr
        ssrc = 0

        rtpPacket = RtpPacket()

        rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)

        return rtpPacket.getPacket()

    def replyRtsp(self, code, seq):
        """Send RTSP reply to the client."""
        if code == self.OK_200:
            message = Rtsp.createRespond(Rtsp.StatusCode.OK, seq, self.clientInfo["session"])
        elif code == self.FILE_NOT_FOUND_404:
            message = Rtsp.createRespond(Rtsp.StatusCode.FILE_NOT_FOUND, seq)
        else:
            message = Rtsp.createRespond(Rtsp.StatusCode.CONNECTION_ERROR, seq)

        connSocket = self.clientInfo['rtspSocket'][0]
        connSocket.send(message.encode())

    def run(self):
        self.recvRtspRequest()
        # threading.Thread(target=self.recvRtspRequest).start()
