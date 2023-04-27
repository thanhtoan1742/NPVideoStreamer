"""
Packet Streaming Protocol
My own protocol to solve the problem of streaming
decrete packets.

Header: 2 bytes, length of payload + 1
Payload
Terminator: 1 bytes, value = 0xED
"""
PACKET_MAX_SIZE = 1 << 14
HEADER_SIZE = 2
TERMINATOR: int = 0xED
PAYLOAD_MAX_SIZE = PACKET_MAX_SIZE - HEADER_SIZE - 1


class Packet:
    def __init__(self, payload: bytearray) -> None:
        self.header = len(payload) & 0xFFFF
        self.payload = payload

    def payload_size(self):
        return self.header

    def encode(self):
        return (
            self.header.to_bytes(HEADER_SIZE, "big")
            + self.payload
            + TERMINATOR.to_bytes(1, "big")
        )

    def __str__(self):
        return f"PS(payload_size={self.payload_size()}, payload={str(self.payload)})"


def decode_header(header: bytes) -> int:
    return int.from_bytes(header, "big")


class WrongTerminatorException(Exception):
    def __init__(self, terminator) -> None:
        if isinstance(terminator, bytes):
            terminator = int.from_bytes(terminator, "big")
        super().__init__(
            "Expected {}, got {}".format(str(hex(TERMINATOR)), str(hex(terminator)))
        )
