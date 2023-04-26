from npvs import ps
import unittest


class TestPs(unittest.TestCase):
    def test_header_value(self):
        packet = ps.Packet(b"x" * 27)
        self.assertEqual(packet.header, 27)

    def test_payload_size(self):
        packet = ps.Packet(b"x" * 27)
        self.assertEqual(packet.payload_size(), 27)

    def test_payload_value(self):
        packet = ps.Packet(b"x" * 27)
        self.assertEqual(packet.payload, b"x" * 27)

    def test_encode(self):
        packet = ps.Packet(b"x" * 27)
        expect = 0x001B_78787878_78787878_78787878_78787878_78787878_78787878_787878_ED
        self.assertEqual(packet.encode(), expect.to_bytes(30, "big"))

    def test_decode_header(self):
        header = (0x001B).to_bytes(2, "big")
        self.assertEqual(ps.decode_header(header), 27)
