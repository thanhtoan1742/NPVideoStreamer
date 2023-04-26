import logging
import socket
from threading import Lock, Thread

from npvs import ps

BUFFER_SIZE = 1 << 10


class PsReceiver:
    def __init__(self, ip: str, logger: logging.Logger) -> None:
        self.ip = ip
        self.logger = logger

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ip, self.port))
        self.port = int(self.socket.getsockname()[1])

        self.bufferLock = Lock()
        self.buffer = bytearray
        self.currentSize = None

        self.recvThread = Thread(target=self._receive_)
        self.recvThread.start()

    def __del__(self) -> None:
        self.recvThread.join()
        self.socket.close()
        self.bufferLock.release()

    def _receive_(self) -> None:
        while True:
            try:
                data = self.socket.recv(BUFFER_SIZE)
                if not data:
                    self.logger.info("TCP session done")
                    return
            except socket.timeout as e:
                self.logger.warning("timed out when waiting for incoming packet")
            except Exception as e:
                self.logger.error(
                    "exception when waiting for incomming packet, e = %s", str(e)
                )
                raise e

            self.bufferLock.acquire()
            self.buffer += data
            self.bufferLock.release()

    def next_payload(self) -> bytes | None:
        with self.bufferLock:
            if len(self.buffer) == 0:
                return
            self.currentSize = ps.decode_header(self.buffer[0])
            self.buffer = self.buffer[1:]

            if len(self.buffer) < self.currentSize:
                return

            payload = self.buffer[self.currentSize]
            self.buffer = self.buffer[self.currentSize :]
            self.currentSize = None

            return payload
