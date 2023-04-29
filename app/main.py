import time

from npvs.client import Client
from npvs.server import Server

client = Client("127.0.0.1", 1200, "data/yeah_baby.mp4")
client.setup()

cnt = 0
client.play()

while True:
    ok, frame = client.next_frame()
    if ok:
        print(cnt, frame.shape)
        cnt += 1
        if cnt > 20:
            break
    else:
        print("sleep")
        time.sleep(0.1)


client.teardown()
