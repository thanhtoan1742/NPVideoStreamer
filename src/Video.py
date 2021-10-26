from typing import Tuple
import numpy as np
import cv2
from kivy.graphics.texture import Texture


def toTexture(image: np.ndarray) -> Texture:
    buffer = cv2.flip(image, 0).tostring()
    texture = Texture.create(size=(image.shape[1], image.shape[0]), colorfmt="bgr")
    texture.blit_buffer(buffer, colorfmt="bgr", bufferfmt="ubyte")
    return texture


class VideoReader:
    def __init__(self, fileName: str) -> None:
        self.fileName = fileName
        self.videoCapture = cv2.VideoCapture(fileName)

    def __del__(self) -> None:
        self.videoCapture.release()

    def nextFrame(self) -> Tuple[bool, np.ndarray]:
        ok, frame = self.videoCapture.read()
        if not ok:
            return False, None
        return True, frame
