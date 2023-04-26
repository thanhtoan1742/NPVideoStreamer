import pickle
from math import floor, sqrt
from queue import PriorityQueue
from threading import Lock
from typing import Tuple

import cv2
import numpy as np

from npvs import rtp


def fit_payload_grey(image: np.ndarray) -> np.ndarray:
    # convert to gray
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # downscale
    h, w = image.shape
    sz = rtp.PAYLOAD_SIZE
    f = sqrt(sz / (h * w))
    h = floor(h * f)
    w = floor(w * f)
    image = cv2.resize(image, (w, h))

    return image


def fit_payload(image: np.ndarray) -> np.ndarray:
    # downscale
    h, w, d = image.shape
    sz = rtp.PAYLOAD_SIZE
    f = sqrt(sz / (h * w * d))
    h = floor(h * f)
    w = floor(w * f)
    image = cv2.resize(image, (w, h))

    return image


class VideoReader:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        self.video_capture = cv2.VideoCapture(filename)

    def __del__(self) -> None:
        self.video_capture.release()

    def next_frame(self):
        ok, frame = self.video_capture.read()
        if not ok:
            return False, None

        return True, frame


class VideoAssembler:
    """
    Assemble rtp packets to frames.
    This class assume there is no packet loss and all packets arrived in other.
    """

    def __init__(self) -> None:
        self.frame_buffer = []
        self.packet_buffer = PriorityQueue()
        self.frame_buffer_lock = Lock()

        self.packet_counter = 0
        self.current_bin_frame = b""

    def add_packet(self, packet: rtp.Packet):
        self.packet_buffer.put(packet)

        while True:
            if self.packet_buffer.empty():
                break

            if self.packet_buffer.queue[0].sequenceNumber() != self.packet_counter:
                break

            p = self.packet_buffer.get()
            self.packet_counter += 1
            self.current_bin_frame += p.payload

            if p.marker():
                frame = pickle.loads(self.current_bin_frame)
                self.current_bin_frame = b""
                self.frame_buffer_lock.acquire()
                self.frame_buffer.append(frame)
                self.frame_buffer_lock.release()

    def next_frame(self) -> Tuple[bool, np.ndarray]:
        ok, frame = False, None
        self.frame_buffer_lock.acquire()
        if len(self.frame_buffer) > 0:
            ok = True
            frame = self.frame_buffer.pop(0)
        self.frame_buffer_lock.release()

        return ok, frame
