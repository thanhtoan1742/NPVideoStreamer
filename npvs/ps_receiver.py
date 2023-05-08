import logging
import socket

from npvs import ps
from npvs.common import get_logger

SOCKET_RECV_SIZE = 1 << 14


class PsReceiver:
    """
    PsReceiver take an socking that is listening to incomming PS packets,
    read incomming PS packets, parse them, check them and yeaid payload of those
    packets.
    """

    def __init__(self, socket: socket.socket) -> None:
        self.socket = socket
        self.socket.settimeout(5)

        self.logger = get_logger("ps-receiver")
        # self.logger.setLevel(logging.DEBUG)

        self.buffer = bytearray()
        self.current_size = None
        self.payload_queue = []

        self.is_done_flag = False

    def _try_parse_buffer_(self):
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

            self.payload_queue.append(payload)

    def _receive_(self) -> None:
        if self.is_done():
            raise Exception("Try to receive data on a closed socket")
        try:
            data, _ = self.socket.recvfrom(SOCKET_RECV_SIZE)
            if not data:
                self.logger.info("TCP session done")
                self.is_done_flag = True
                return

            self.logger.debug("received packet size = %d", len(data))
            self.buffer += data
        except socket.timeout as e:
            self.logger.warning("timed out when waiting for incoming packet")
            pass
        except Exception as e:
            self.logger.error(
                "exception when waiting for incomming packet, e = %s", str(e)
            )
            self.is_done_flag = True
            raise e

    def is_done(self) -> bool:
        return self.is_done_flag

    def next_payload(self) -> bytes:
        while len(self.payload_queue) == 0:
            if self.is_done():
                return
            self._receive_()
            self._try_parse_buffer_()

        payload = self.payload_queue[0]
        self.payload_queue.pop(0)
        return payload
