import time
from unittest.mock import Mock

from npvs import ps
from npvs.common import get_logger
from npvs.ps_receiver import BUFFER_SIZE, PsReceiver

with open("server-data.bin", "rb") as f:
    sd = f.read()

with open("client-data.bin", "rb") as f:
    cd = f.read()


def make_socket(data):
    cur = 0

    def recv(*args):
        nonlocal cur, data
        if cur >= len(data):
            return None
        nex = min(cur + BUFFER_SIZE, len(data))
        res = data[cur:nex]
        cur = nex
        return res

    socket = Mock()
    socket.recv.side_effect = recv

    return socket


receiver = PsReceiver(make_socket(cd), get_logger("main"))
while True:
    if receiver.is_done():
        break
    payload = receiver.next_payload()
    if payload:
        print(len(payload))
    else:
        print(None)
