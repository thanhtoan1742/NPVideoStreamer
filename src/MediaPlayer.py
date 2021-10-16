from common import *
from threading import Event, Thread

class MediaPlayer:
    """Player class manage state of a media player"""
    INIT = 0
    READY = 1
    PLAYING = 2

    def __init__(self) -> None:
        self.state = self.INIT
        self.playingFlag = Event()

    def setup(self) -> bool:
        if self.state != self.INIT:
            return False

        if not self._setup_():
            return False

        self.state = self.READY
        return True

    def play(self) -> bool:
        if self.state != self.READY:
            return False

        if not self._play_():
            return False

        self.state = self.PLAYING
        self.stream()
        return True

    def pause(self) -> bool:
        if self.state != self.PLAYING:
            return False

        if not self._pause_():
            return False

        self.state = self.READY
        return True

    def teardown(self) -> bool:
        if self.state != self.READY and self.state != self.PLAYING:
            return False

        if not self._teardown_():
            return False

        self.state = self.INIT
        return True

    def stream(self) -> None:
        def target():
            while True:
                self.playingFlag.wait(0.05)
                if not self.playingFlag.is_set():
                    break

                self._stream_()

        Thread(target=target).start()



    def _setup_(self) -> bool:
        raise NotImplementedError

    def _play_(self) -> bool:
        raise NotImplementedError

    def _pause_(self) -> bool:
        raise NotImplementedError

    def _teardown_(self) -> bool:
        raise NotImplementedError

    def _stream_(self) -> None:
        raise NotImplementedError

