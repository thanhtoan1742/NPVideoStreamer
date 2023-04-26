"""
Packet Streaming Protocol
My own protocol to solve the problem of streaming
decrete packets.

Header: 2 bytes, length of payload + 1
Payload
Terminator: 1 bytes, value = 1101 0011
"""
HEADER_SIZE = 2
TERMINATOR = (0b11010011).to_bytes(1, "big")


class Packet:
    def __init__(self, payload: bytearray) -> None:
        self.header = len(payload) & 0xFFFF
        self.payload = payload

    def payload_size(self):
        return self.header

    def encode(self):
        return self.header.to_bytes(HEADER_SIZE, "big") + self.payload + TERMINATOR

    def __str__(self):
        return f"PS(payload_size={self.payload_size()}, payload={str(self.payload)})"


def decode_header(header: bytes) -> int:
    return int.from_bytes(header, "big")
