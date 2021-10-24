from typing import Tuple
from PIL import Image

class VideoAssembler:
    def __init__(self) -> None:
        raise NotImplementedError
        self.frames = {}
        self.frameQueue = []

    def nextFrame(self) -> Tuple[bool, Image.Image]:
        raise NotImplementedError
        return (False, None)

    def add(self, data: dict) -> None:
        raise NotImplementedError

