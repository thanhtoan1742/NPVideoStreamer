from typing import Tuple
import cv2
from math import floor, sqrt
import numpy as np
from PIL import Image, ImageTk

import Rtp


def cvImage2PilImage(image: np.ndarray) -> Image.Image:
    b, g, r = cv2.split(image)
    image = cv2.merge((r, g, b))
    return Image.fromarray(image)


def fitPayload(image: Image.Image) -> Image.Image:
    # convert to gray scale
    image = image.convert("L")

    # resize
    sz = Rtp.PAYLOAD_SIZE
    w, h = image.size
    f = sqrt(sz / (h*w))
    w = floor(w*f)
    h = floor(h*f)

    image = image.resize((w, h))
    return image



class VideoReader:
    def __init__(self, fileName: str) -> None:
        self.fileName = fileName
        self.videoCapture = cv2.VideoCapture(fileName)

    def __del__(self) -> None:
        self.videoCapture.release()

    def nextFrame(self) -> Tuple[bool, Image.Image]:
        ok, frame = self.videoCapture.read()
        if not ok:
            return False, None
        return True, cvImage2PilImage(frame)
