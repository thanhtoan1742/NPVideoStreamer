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

        self.buffer_lock = Lock()
        self.buffer = bytearray
        self.current_size = None

        self.recv_thread = Thread(target=self._receive_)
        self.recv_thread.start()

    def __del__(self) -> None:
        self.recv_thread.join()
        self.socket.close()
        self.buffer_lock.release()

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

            self.buffer_lock.acquire()
            self.buffer += data
            self.buffer_lock.release()

    def next_payload(self) -> bytes | None:
        with self.buffer_lock:
            if len(self.buffer) == 0:
                return
            self.current_size = ps.decode_header(self.buffer[0])
            self.buffer = self.buffer[1:]

            if len(self.buffer) < self.current_size:
                return

            payload = self.buffer[self.current_size]
            self.buffer = self.buffer[self.current_size :]
            self.current_size = None

            return payload
