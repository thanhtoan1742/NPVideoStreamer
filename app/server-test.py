import socket
import cv2
import pickle
from npvs import ps, rtp
import yappi

FILENAME = "data/yeah_baby.mp4"
IP = "127.0.0.1"
PORT = 0


vc = cv2.VideoCapture(FILENAME)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((IP, PORT))
server.listen(1)
print(server.getsockname())


conn, addr = server.accept()
print("connected to", addr)
size = 0
yappi.start()
while True:
    ok, frame = vc.read()
    if not ok:
        break
    bin = pickle.dumps(frame)
    bin = ps.Packet(rtp.Packet(bytes(rtp.HEADER_SIZE), bin).encode()).encode()
    size += len(bin)
    conn.sendall(bin)
yappi.stop()

print("total", size)
vc.release()
server.close()
conn.close()

yappi.get_func_stats().print_all()
thread_stats = yappi.get_thread_stats()
thread_stats.print_all()
for thread_stat in thread_stats:
    print("\n\nfunc stats for thread %s (%d)" % (thread_stat.name, thread_stat.id))
    yappi.get_func_stats(ctx_id=thread_stat.id).print_all()
