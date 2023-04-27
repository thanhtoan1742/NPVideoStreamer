from threading import Event, Thread

from npvs.common import *


class MediaPlayer:
    """Player class manage state of a media player"""

    INIT = 0
    READY = 1
    PLAYING = 2

    def __init__(self) -> None:
        self.state = self.INIT
        self.playing_flag = Event()
        self.streaming_flag = Event()
        self.stream_thread: Thread = None
        self.fps = 60

    def setup(self) -> bool:
        if self.state != self.INIT:
            return False

        if not self._setup_():
            return False

        self.streaming_flag.set()
        self.playing_flag.clear()
        self.stream_thread = Thread(target=self.stream)
        self.stream_thread.start()
        self.state = self.READY
        return True

    def play(self) -> bool:
        if self.state != self.READY:
            return False

        if not self._play_():
            return False

        self.playing_flag.set()
        self.state = self.PLAYING
        return True

    def pause(self) -> bool:
        if self.state != self.PLAYING:
            return False

        if not self._pause_():
            return False

        self.playing_flag.clear()
        self.state = self.READY

        return True

    def teardown(self) -> bool:
        if self.state != self.READY and self.state != self.PLAYING:
            return False

        if self.state == self.PLAYING:
            self.pause()

        if not self._teardown_():
            return False

        self.playing_flag.clear()
        self.streaming_flag.clear()
        self.stream_thread.join()
        self.state = self.INIT
        return True

    def stream(self) -> None:
        while self.streaming_flag.is_set():
            if not self.playing_flag.is_set():
                continue
            self._stream_()

    def _stream_(self) -> None:
        raise NotImplementedError

    def _setup_(self) -> bool:
        raise NotImplementedError

    def _play_(self) -> bool:
        raise NotImplementedError

    def _pause_(self) -> bool:
        raise NotImplementedError

    def _teardown_(self) -> bool:
        raise NotImplementedError
