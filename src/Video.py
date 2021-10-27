import pickle
from typing import Tuple
from math import floor, sqrt
from threading import Lock
import cv2
import numpy as np
from queue import PriorityQueue

import Rtp



def fitPayloadGrey(image: np.ndarray) -> np.ndarray:
    # convert to gray
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # downscale
    h, w = image.shape
    sz = Rtp.PAYLOAD_SIZE
    f = sqrt(sz / (h*w))
    h = floor(h*f)
    w = floor(w*f)
    image = cv2.resize(image, (w, h))

    return image



def fitPayload(image: np.ndarray) -> np.ndarray:
    # downscale
    h, w, d = image.shape
    sz = Rtp.PAYLOAD_SIZE
    f = sqrt(sz / (h*w*d))
    h = floor(h*f)
    w = floor(w*f)
    image = cv2.resize(image, (w, h))

    return image

class VideoReader:
    def __init__(self, fileName: str) -> None:
        self.fileName = fileName
        self.videoCapture = cv2.VideoCapture(fileName)

    def __del__(self) -> None:
        self.videoCapture.release()

    def nextFrame(self):
        ok, frame = self.videoCapture.read()
        if not ok:
            return False, None

        return True, frame


class VideoAssembler:
    """
    Assemble RTP packets to frames.
    This class assume there is no packet loss and all packets arrived in other.
    """
    def __init__(self) -> None:
        self.frameBuffer = []
        self.packetBuffer = PriorityQueue()
        self.frameBufferLock = Lock()

        self.packetCounter = 0
        self.currentBinFrame = b""


    def addPacket(self, packet: Rtp.Packet):
        self.packetBuffer.put(packet)
        print(self.packetBuffer.queue[0])

        while True:
            if self.packetBuffer.empty():
                break

            if self.packetBuffer.queue[0].sequenceNumber() != self.packetCounter:
                break

            p = self.packetBuffer.get()
            self.packetCounter += 1
            self.currentBinFrame += p.payload

            if p.marker():
                frame = pickle.loads(self.currentBinFrame)
                self.currentBinFrame = b""
                self.frameBufferLock.acquire()
                self.frameBuffer.append(frame)
                self.frameBufferLock.release()



    def nextFrame(self) -> Tuple[bool, np.ndarray]:
        ok, frame = False, None
        self.frameBufferLock.acquire()
        if len(self.frameBuffer) > 0:
            ok = True
            frame = self.frameBuffer.pop(0)
        self.frameBufferLock.release()

        return ok, frame

