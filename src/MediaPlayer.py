from common import *
from threading import Event, Thread
import time

class MediaPlayer:
    """Player class manage state of a media player"""
    INIT = 0
    READY = 1
    PLAYING = 2

    def __init__(self) -> None:
        self.state = self.INIT
        self.playingFlag = Event()
        self.streamThread: Thread = None
        self.fps = 60

    def setup(self) -> bool:
        if self.state != self.INIT:
            return False

        if not self._setup_():
            return False

        self.state = self.READY
        self.playingFlag.clear()
        return True

    def play(self) -> bool:
        if self.state != self.READY:
            return False

        if not self._play_():
            return False

        self.state = self.PLAYING
        self.playingFlag.set()

        self.streamThread = Thread(target=self.stream)
        self.streamThread.start()

        return True


    def pause(self) -> bool:
        if self.state != self.PLAYING:
            return False

        if not self._pause_():
            return False

        self.playingFlag.clear()
        self.state = self.READY

        self.streamThread.join()
        return True

    def teardown(self) -> bool:
        if self.state != self.READY and self.state != self.PLAYING:
            return False

        if self.state == self.PLAYING:
            self.pause()

        if not self._teardown_():
            return False

        self.playingFlag.clear()
        self.state = self.INIT
        return True

    def stream(self) -> None:
        while True:
            if not self.playingFlag.is_set():
                break
            time.sleep(1/self.fps)

            print("before processing frame")
            self.processFrame()
            print("after processing frame")

    def _setup_(self) -> bool:
        raise NotImplementedError

    def _play_(self) -> bool:
        raise NotImplementedError

    def _pause_(self) -> bool:
        raise NotImplementedError

    def _teardown_(self) -> bool:
        raise NotImplementedError

    def processFrame(self) -> None:
        raise NotImplementedError

