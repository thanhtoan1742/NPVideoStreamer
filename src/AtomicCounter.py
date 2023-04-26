from threading import Lock


class AtomicCounter:
    def __init__(self) -> None:
        self.lock = Lock()
        self.counter = 0

    def increment(self) -> None:
        self.lock.acquire()
        self.counter += 1
        self.lock.release()

    def get(self) -> int:
        self.lock.acquire()
        res = self.counter
        self.lock.release()
        return res

    def getThenIncrement(self) -> int:
        self.lock.acquire()
        res = self.counter
        self.counter += 1
        self.lock.release()
        return res
