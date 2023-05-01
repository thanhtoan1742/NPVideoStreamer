import logging
import pickle
from multiprocessing import Queue

import cv2
import numpy as np

from npvs import rtp
from npvs.common import get_logger


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
        self.current_bin_frame = b""

        self.frame_queue = frame_queue

    def add_packet(self, packet: rtp.Packet):
        self.logger.debug("adding packet = %s", str(packet))
        if packet.sequence_number() != (self.packet_counter & 0xFFFF):
            raise Exception(
                f"unmatched sequence number, expected {self.packet_counter}, got {packet.sequence_number()}"
            )
        self.packet_counter += 1
        self.current_bin_frame += packet.payload

        if packet.marker():
            frame = pickle.loads(self.current_bin_frame)
            self.logger.debug("assembled frame shape = %s", str(frame.shape))
            self.current_bin_frame = b""
            self.frame_queue.put(frame)
