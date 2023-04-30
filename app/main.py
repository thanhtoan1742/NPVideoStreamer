import time

from npvs.client import Client
from npvs.server import Server

client = Client("192.168.1.8", 1200, "data/suprise.mp4")
client.setup()

cnt = 0
client.play()

while True:
    ok, frame = client.next_frame()
    if ok:
        print(cnt, frame.shape)
        cnt += 1


client.teardown()
