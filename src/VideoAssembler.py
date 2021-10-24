from typing import Tuple
import numpy as np


Frame = np.ndarray


class RtpVideoAssembler:
    def __init__(self) -> None:
        raise NotImplementedError
        self.frames = {}
        self.frameQueue = []

    def nextFrame(self) -> Tuple[bool, Frame]:
        raise NotImplementedError
        return (False, None)

    def add(self, data: dict) -> None:
        raise NotImplementedError

