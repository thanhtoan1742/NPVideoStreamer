import logging
import socket
from threading import Lock, Thread

from npvs import ps
from npvs.dumper import Dumper

BUFFER_SIZE = 1 << 14


class PsReceiver:
    """
    PsReceiver take an socking that is listening to incomming PS packets,
    read incomming PS packets, parse them, check them and yeaid payload of those
    packets.
    """

    def __init__(self, socket: socket.socket, logger: logging.Logger) -> None:
        self.socket = socket
        self.logger = logger

        self.lock = Lock()
        self.buffer = bytearray()
        self.current_size = None

        # self.dumper = Dumper("client-data.bin")

        self.recv_thread = Thread(target=self._receive_)
        self.recv_thread.start()

    def __del__(self) -> None:
        self.recv_thread.join()

    def _receive_(self) -> None:
        self.socket.settimeout(5)
        while True:
            try:
                data = self.socket.recv(BUFFER_SIZE)
                if not data:
                    self.logger.info("TCP session done")
                    return
                self.logger.debug("received data, data size = %s", len(data))
                with self.lock:
                    self.buffer += data
                # self.dumper.append(data)
            except socket.timeout as e:
                # self.logger.warning("timed out when waiting for incoming packet")
                pass
            except Exception as e:
                self.logger.error(
                    "exception when waiting for incomming packet, e = %s", str(e)
                )
                raise e

    def is_done(self) -> bool:
        with self.lock:
            if len(self.buffer) > 0:
                return False
        return not self.recv_thread.is_alive()

    def next_payload(self) -> bytes | None:
        if self.is_done():
            return

        with self.lock:
            if self.current_size == None:
                if len(self.buffer) < 2:
                    return
                self.current_size = ps.decode_header(self.buffer[:2])
                self.buffer = self.buffer[2:]

            if len(self.buffer) < self.current_size + 1:
                return

            self.logger.debug(
                "decode buffer, payload size = %s, buffer size = %s",
                self.current_size,
                len(self.buffer),
            )
            payload = self.buffer[: self.current_size]
            terminator = self.buffer[self.current_size]
            self.buffer = self.buffer[self.current_size + 1 :]
            self.current_size = None

            if terminator != ps.TERMINATOR:
                e = ps.WrongTerminatorException(terminator)
                self.logger.error(str(e))
                raise e

            return payload
