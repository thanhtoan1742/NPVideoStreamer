from npvs.client import Client
from npvs.server import Server
import time
import yappi


yappi.start()
client = Client("127.0.0.1", 1200, "data/yeah_baby.mp4")
client.setup()

cnt = 0
client.play()

while not client.ps_receiver.is_done():
    ok, frame = client.next_frame()
    if ok:
        cnt += 1
        print(cnt, frame.shape)
        if cnt > 20:
            break
    else:
        time.sleep(1)


client.teardown()
yappi.stop()

thread_stats = yappi.get_thread_stats()
thread_stats.print_all()
for thread_stat in thread_stats:
    print("\n\nfunc stats for thread %s (%d)" % (thread_stat.name, thread_stat.id))
    yappi.get_func_stats(ctx_id=thread_stat.id).print_all()
