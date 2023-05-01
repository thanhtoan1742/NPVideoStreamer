import multiprocessing as mp
import time

from npvs.client import Client

if __name__ == "__main__":
    mp.set_start_method("spawn")

    client = Client("127.0.0.1", 1200, "data/suprise.mp4")
    client.setup()

    cnt = 0
    client.play()

    while True:
        ok, frame = client.next_frame()
        if ok:
            print(cnt, frame.shape)
            cnt += 1
        if cnt > 50:
            break

    client.teardown()
