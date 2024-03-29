from npvs.common import *
from npvs.ps import PAYLOAD_MAX_SIZE as PS_PAYLOAD_MAX_SIZE

PACKET_MAX_SIZE = PS_PAYLOAD_MAX_SIZE
HEADER_SIZE = (32 * 3) >> 3
PAYLOAD_SIZE = PACKET_MAX_SIZE - HEADER_SIZE


class Packet:
    def __init__(self, header: bytearray, payload: bytearray) -> None:
        assert len(header) == HEADER_SIZE
        self.header = header
        self.payload = payload

    def __eq__(self, o: object) -> bool:
        return self.sequence_number() == o.sequence_number()

    def __lt__(self, o: object) -> bool:
        return self.sequence_number() < o.sequence_number()

    def __str__(self) -> str:
        return f"[{self.sequence_number()} {self.marker()}]"
        return (
            f"marker: {self.marker()}\n"
            f"sequenceNumber: {self.sequence_number()}\n"
            f"timestamp: {self.timestamp()}\n"
        )  # f"payload: {self.payload}\n" \

    def encode(self) -> bytearray:
        """Return encoded RTP packet"""
        return self.header + self.payload

    def version(self) -> int:
        """Return RTP version"""
        return int(self.header[0] >> 6) & 3

    def padding(self) -> int:
        """Return RTP padding"""
        return int(self.header[0] >> 5) & 1

    def extension(self) -> int:
        """Return RTP extension"""
        return int(self.header[0] >> 4) & 1

    def marker(self) -> int:
        """Return RTP marker"""
        return int(self.header[1] >> 7) & 1

    def payload_type(self) -> int:
        """Return payload type."""
        pt = self.header[1] & 127
        return int(pt)

    def sequence_number(self) -> int:
        """Return RTP sequence number"""
        seqNum = self.header[2] << 8 | self.header[3]
        return int(seqNum)

    def timestamp(self) -> int:
        """Return RTP timestamp"""
        timestamp = (
            self.header[4] << 24
            | self.header[5] << 16
            | self.header[6] << 8
            | self.header[7]
        )
        return int(timestamp)

    def ssrc(self) -> int:
        """Return RTP timestamp"""
        timestamp = (
            self.header[8] << 24
            | self.header[9] << 16
            | self.header[10] << 8
            | self.header[11]
        )
        return int(timestamp)

    def to_dict(self) -> dict:
        return {
            "version": self.version(),
            # "padding": self.padding(),
            # "extension": self.extension(),
            # "csrcCount": self.csrcCount(),
            "marker": self.marker(),
            "payloadType": self.payload_type(),
            "sequenceNumber": self.sequence_number(),
            "timestamp": self.timestamp(),
            "ssrc": self.ssrc(),
            # "csrcList": p.csrcList(),
            "payload": self.payload,
        }


def decode(data: bytearray) -> Packet:
    return Packet(data[:HEADER_SIZE], data[HEADER_SIZE:])


def packet_from_dict(data: dict = {}) -> Packet:
    header = bytearray(HEADER_SIZE)

    header[0] = (data["version"] << 6) & 0xFF

    # currently do not support padding, defaults to 0
    # header |= (data["padding"] << 5) & 0xFF

    # currently do not support extension, defaults to 0
    # header[0] |= (data["extension"] << 4) & 0xFF

    # currently do not support csrcCount, defaults to 0
    # header |= data["csrcCount"]

    header[1] = (data["marker"] << 7) & 0xFF

    header[1] |= data["payloadType"] & 0xFF

    header[2] = (data["sequenceNumber"] >> 8) & 0xFF
    header[3] = data["sequenceNumber"] & 0xFF

    header[4] = (data["timestamp"] >> 24) & 0xFF
    header[5] = (data["timestamp"] >> 16) & 0xFF
    header[6] = (data["timestamp"] >> 8) & 0xFF
    header[7] = data["timestamp"] & 0xFF

    header[8] = (data["ssrc"] >> 24) & 0xFF
    header[9] = (data["ssrc"] >> 16) & 0xFF
    header[10] = (data["ssrc"] >> 8) & 0xFF
    header[11] = data["ssrc"] & 0xFF

    # header += data["csrcList"].

    payload = data["payload"]

    return Packet(header, payload)
