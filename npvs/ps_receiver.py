import ctypes
import logging
import socket
from multiprocessing import Array, Event, Lock, Process, Queue

from npvs import ps
from npvs.common import get_logger
from npvs.dumper import Dumper

SOCKET_RECV_SIZE = 1 << 14


class PsReceiver:
    """
    PsReceiver take an socking that is listening to incomming PS packets,
    read incomming PS packets, parse them, check them and yeaid payload of those
    packets.
    """

    def __init__(self, socket: socket.socket) -> None:
        self.socket = socket
        self.logger = get_logger("ps-receiver")
        # self.logger.setLevel(logging.DEBUG)

        self.buffer = bytearray()
        self.current_size = None
        self.payload_queue = Queue()

        # self.dumper = Dumper("client-data.bin")

        self.recv_thread = Process(target=self._receive_, args=[self.payload_queue])
        self.is_done_flag = Event()
        self.recv_thread.start()

    def __del__(self) -> None:
        self.recv_thread.join()

    def _try_parse_buffer_(self, queue: Queue):
        while True:
            if self.current_size == None:
                if len(self.buffer) < 2:
                    break
                self.current_size = ps.decode_header(self.buffer[:2])
                self.buffer = self.buffer[2:]

            if len(self.buffer) < self.current_size + 1:
                break

            payload = self.buffer[: self.current_size]
            terminator = self.buffer[self.current_size]
            self.buffer = self.buffer[self.current_size + 1 :]
            self.current_size = None

            if terminator != ps.TERMINATOR:
                e = ps.WrongTerminatorException(terminator)
                self.logger.error(str(e))
                raise e

            queue.put(payload)

    def _receive_(self, queue: Queue) -> None:
        self.socket.settimeout(5)
        while True:
            try:
                data = self.socket.recv(SOCKET_RECV_SIZE)
                if not data:
                    self.logger.info("TCP session done")
                    self.is_done_flag.set()
                    return

                self.logger.debug("received packet size = %d", len(data))
                self.buffer += data
                self._try_parse_buffer_(queue)
            except socket.timeout as e:
                self.logger.warning("timed out when waiting for incoming packet")
                pass
            except Exception as e:
                self.logger.error(
                    "exception when waiting for incomming packet, e = %s", str(e)
                )
                self.is_done_flag.set()
                raise e

    def is_done(self) -> bool:
        if not self.payload_queue.empty():
            return False
        return self.is_done_flag.is_set()

    def next_payload(self) -> bytes | None:
        if not self.payload_queue.empty():
            return self.payload_queue.get()
        return None
