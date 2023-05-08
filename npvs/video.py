import logging
import pickle
from multiprocessing import Queue
from queue import PriorityQueue

import cv2
import numpy as np
import math

from npvs import rtp
from npvs.common import get_logger


def fit_payload_grey(image: np.ndarray) -> np.ndarray:
    # convert to gray
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # downscale
    h, w = image.shape
    sz = rtp.PAYLOAD_SIZE
    f = math.sqrt(sz / (h * w))
    h = math.floor(h * f)
    w = math.floor(w * f)
    image = cv2.resize(image, (w, h))

    return image


def fit_payload(image: np.ndarray) -> np.ndarray:
    # downscale
    h, w, d = image.shape
    sz = rtp.PAYLOAD_SIZE
    f = math.sqrt(sz / (h * w * d))
    h = math.floor(h * f)
    w = math.floor(w * f)
    image = cv2.resize(image, (w, h))

    return image


class VideoReader:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        # do not initialize now to advoid cv2 bug on multiprocess
        # https://github.com/opencv/opencv/issues/5150
        self.video_capture = None
        self.frame_counter = 0

    def __del__(self) -> None:
        if self.video_capture != None:
            self.video_capture.release()

    def next_frame(self):
        if self.video_capture == None:
            self.video_capture = cv2.VideoCapture(self.filename)
        ok, frame = self.video_capture.read()
        if not ok:
            return False, None

        self.frame_counter += 1
        return True, frame


class VideoAssembler:
    """
    Assemble rtp packets to frames.
    """

    def __init__(self, frame_queue: Queue) -> None:
        self.logger = get_logger("video-assembler")
        # self.logger.setLevel(logging.DEBUG)

        self.packet_counter = 0
        self.packet_queue = PriorityQueue()

        self.frame_queue = frame_queue

    def add_packet(self, packet: rtp.Packet):
        self.logger.debug("adding packet = %s", str(packet))
        self.packet_queue.put(packet)
        # if miss buffering for 90 packet, ignore the packet counter
        while (
            packet.sequence_number() == (self.packet_counter & 0xFFFF)
            or self.packet_queue.qsize() > 90
        ):
            packet = self.packet_queue.get()
            self.packet_counter = packet.sequence_number() + 1
            frame = pickle.loads(packet.payload)
            self.frame_queue.put(frame)
            self.logger.debug("got frame shape = %s", str(frame.shape))
