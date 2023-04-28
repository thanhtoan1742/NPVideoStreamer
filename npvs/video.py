import pickle
from queue import PriorityQueue
from multiprocessing import Lock
from typing import Tuple

import cv2
import numpy as np

from npvs import rtp


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

    def __init__(self) -> None:
        self.packet_buffer = PriorityQueue()
        self.packet_counter = 0

        self.frame_buffer = []
        self.frame_buffer_lock = Lock()
        self.current_bin_frame = b""

    def add_packet(self, packet: rtp.Packet):
        self.packet_buffer.put(packet)

        while True:
            if self.packet_buffer.empty():
                break

            if self.packet_buffer.queue[0].sequence_number() != self.packet_counter:
                break

            p = self.packet_buffer.get()
            self.packet_counter += 1
            self.current_bin_frame += p.payload

            if p.marker():
                frame = pickle.loads(self.current_bin_frame)
                self.current_bin_frame = b""
                with self.frame_buffer_lock:
                    self.frame_buffer.append(frame)

    def next_frame(self) -> Tuple[bool, np.ndarray]:
        with self.frame_buffer_lock:
            if len(self.frame_buffer) > 0:
                return True, self.frame_buffer.pop(0)

        return False, None
