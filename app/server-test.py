import cProfile
import logging
import pickle
import pstats
import socket
from multiprocessing import Process

import cv2

from npvs import ps, rtp

FILENAME = "data/yeah_baby.mp4"
IP = "127.0.0.1"
PORT = 1201


def run(conn):
    ch = logging.FileHandler("server-test.log", "w+")
    logger = logging.Logger("server-test")
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)

    logger.debug("started")
    logger.debug("%s", str(conn))

    vc = cv2.VideoCapture(FILENAME)
    logger.debug("%s", str(vc))

    pr = cProfile.Profile()
    pr.enable()

    size = 0
    while True:
        logger.debug("in while")
        ok, frame = vc.read()
        if not ok:
            logger.debug("cant read frame")
            break
        logger.debug("read frame, shape = %s", str(frame.shape))
        bin = pickle.dumps(frame)
        bin = ps.Packet(rtp.Packet(bytes(rtp.HEADER_SIZE), bin).encode()).encode()
        size += len(bin)
        conn.sendall(bin)
        logger.debug("sent data, size = %d", len(bin))
    logger.debug("out while")

    print("total", size)
    logger.info("total size %d", size)
    vc.release()
    logger.debug("done")

    pr.disable()
    stat = pstats.Stats(pr)
    stat.strip_dirs().sort_stats("cumtime").dump_stats("server-test.prof")


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, PORT))
server.listen(1)
print(server.getsockname())

conn, addr = server.accept()
print("connected to", addr)

p = Process(target=run, args=[conn])
p.start()
p.join()

server.close()
conn.close()
