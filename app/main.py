from unittest.mock import Mock

from tests.test_ps_receiver import make_recv

s = Mock()
s.recv.side_effect = make_recv()


from npvs.common import get_logger
from npvs.ps_receiver import PsReceiver

r = PsReceiver(s, get_logger("client"))
print(r.is_done())
print(r.next_payload())
print(r.is_done())
print(r.next_payload())
print(r.is_done())
print(r.next_payload())
print(r.is_done())
print(r.next_payload())
print(r.is_done())
print(r.next_payload())
print(r.is_done())
