import sys
import yappi

from npvs.server import Server

try:
    port = int(sys.argv[1])
except:
    print("Usage: python Server.py rtspPort\n")

yappi.start()
app = Server("127.0.0.1", port)
app.run()
yappi.stop()

thread_stats = yappi.get_thread_stats()
thread_stats.print_all()
for thread_stat in thread_stats:
    print("\n\nfunc stats for thread %s (%d)" % (thread_stat.name, thread_stat.id))
    yappi.get_func_stats(ctx_id=thread_stat.id).print_all()
