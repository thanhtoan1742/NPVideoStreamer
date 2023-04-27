import time
from unittest.mock import Mock

import pytest

from npvs import ps, ps_receiver
from npvs.common import get_logger


def make_recv():
    idx = 0
    data = [
        ps.Packet(b"1").encode() + ps.Packet(b"2").encode(),
        ps.Packet(b"3").encode(),
    ]

    def recv(*args):
        nonlocal idx
        if idx < len(data):
            res = data[idx]
            idx += 1
        else:
            res = None
        return res

    return recv


@pytest.fixture
def socket():
    mock = Mock()
    mock.recv.side_effect = make_recv()
    return mock


def test_is_done(socket):
    receiver = ps_receiver.PsReceiver(socket, get_logger("null"))
    assert not receiver.is_done()
    receiver.next_payload()
    assert not receiver.is_done()
    receiver.next_payload()
    assert not receiver.is_done()
    receiver.next_payload()
    assert receiver.is_done()


def test_next_payload(socket):
    receiver = ps_receiver.PsReceiver(socket, get_logger("null"))
    time.sleep(2)
    assert receiver.next_payload() == b"1"
    assert receiver.next_payload() == b"2"
    assert receiver.next_payload() == b"3"
    assert receiver.next_payload() == None
