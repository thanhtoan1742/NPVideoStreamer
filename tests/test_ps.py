from npvs import ps


def test_header_value():
    packet = ps.Packet(b"x" * 27)
    assert packet.header == 27


def test_payload_size():
    packet = ps.Packet(b"x" * 27)
    assert packet.payload_size() == 27


def test_payload_value():
    packet = ps.Packet(b"x" * 27)
    assert packet.payload == b"x" * 27


def test_encode():
    packet = ps.Packet(b"x" * 27)
    expect = 0x001B_78787878_78787878_78787878_78787878_78787878_78787878_787878_ED
    assert packet.encode() == expect.to_bytes(30, "big")


def test_decode_header():
    header = (0x001B).to_bytes(2, "big")
    assert ps.decode_header(header) == 27
