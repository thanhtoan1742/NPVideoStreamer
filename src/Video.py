from typing import Tuple
from math import floor, sqrt
from threading import Thread
import cv2
import numpy as np
from kivy.graphics.texture import Texture

import Rtp



def toTextureGrey(image: np.ndarray) -> Texture:
    buffer = cv2.flip(image, 0).tostring()
    texture = Texture.create(size=(image.shape[1], image.shape[0]), colorfmt="luminance")
    texture.blit_buffer(buffer, colorfmt="luminance", bufferfmt="ubyte")
    return texture


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



def toTexture(image: np.ndarray) -> Texture:
    buffer = cv2.flip(image, 0).tostring()
    texture = Texture.create(size=(image.shape[1], image.shape[0]), colorfmt="bgr")
    texture.blit_buffer(buffer, colorfmt="bgr", bufferfmt="ubyte")
    return texture


def fitPayload(image: np.ndarray) -> np.ndarray:
    # downscale
    print(image.shape)
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
