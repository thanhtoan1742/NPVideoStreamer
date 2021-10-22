import sys
from time import time

from common import *

HEADER_SIZE = 32 * 3
PAYLOAD_SIZE = SOCKET_BUFFER_SIZE - HEADER_SIZE

def decode(data: bytearray) -> dict:
    p = Packet()
    p.header = data[:HEADER_SIZE >> 3]
    p.payload = data[HEADER_SIZE >> 3:]
    return {
        "version": p.version(),
        "padding": p.padding(),
        "extension": p.extension(),
        # "csrcCount": p.csrcCount(),
        "marker": p.marker(),
        "payloadType": p.payloadType(),
        "sequenceNumber": p.sequenceNumber(),
        "timestamp": p.timestamp(),
        "ssrc": p.ssrc(),
        # "csrcList": p.csrcList(),
        "payload": p.payload,
    }


class Packet:
    def __init__(self, data: dict = {}) -> None:
        self.header = bytearray(HEADER_SIZE >> 3)
        try:
            self.header[0] = (data["version"] << 6) & 0xFF

            # currently do not support padding, default to 0
            # self.header |= (data["padding"] << 5) & 0xFF

            self.header[0] |= (data["extension"] << 4) & 0xFF

            # currently do not support csrcCount, default to 0
            # self.header |= data["csrcCount"]

            self.header[1] = (data["marker"] << 7) & 0xFF

            self.header[1] |= data["payloadType"] & 0xFF

            self.header[2] = (data["sequenceNumber"] >> 8) & 0xFF
            self.header[3] = data["sequenceNumber"] & 0xFF

            self.header[4] = (data["timestamp"] >> 24) & 0xFF
            self.header[5] = (data["timestamp"] >> 16) & 0xFF
            self.header[6] = (data["timestamp"] >> 8) & 0xFF
            self.header[7] = data["timestamp"] & 0xFF

            self.header[8] = (data["ssrc"] >> 24) & 0xFF
            self.header[9] = (data["ssrc"] >> 16) & 0xFF
            self.header[10] = (data["ssrc"] >> 8) & 0xFF
            self.header[11] = data["ssrc"] & 0xFF

            # self.header += data["csrcList"].

            self.payload = data["payload"]
        except:
            self.payload = bytearray(PAYLOAD_SIZE >> 3)

    def __str__(self) -> str:
        return f"version: {self.version()}\n" \
            f"padding: {self.padding()}\n" \
            f"extension: {self.extension()}\n" \
            f"marker: {self.marker()}\n" \
            f"payloadType: {self.payloadType()}\n" \
            f"sequenceNumber: {self.sequenceNumber()}\n" \
            f"timestamp: {self.timestamp()}\n" \
            f"ssrc: {self.ssrc()}\n" \
            f"payload: {self.payload}\n"



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

    def payloadType(self) -> int:
        """Return payload type."""
        pt = self.header[1] & 127
        return int(pt)

    def sequenceNumber(self) -> int:
        """Return RTP sequence number"""
        seqNum = self.header[2] << 8 | self.header[3]
        return int(seqNum)

    def timestamp(self) -> int:
        """Return RTP timestamp"""
        timestamp = self.header[4] << 24 | self.header[5] << 16 | self.header[6] << 8 | self.header[7]
        return int(timestamp)

    def ssrc(self) -> int:
        """Return RTP timestamp"""
        timestamp = self.header[8] << 24 | self.header[9] << 16 | self.header[10] << 8 | self.header[11]
        return int(timestamp)

    def getPayload(self) -> int:
        """Return RTP payload"""
        return self.payload

