import sys

from npvs.server import Server

try:
    port = int(sys.argv[1])
except:
    print("Usage: python Server.py rtspPort\n")

app = Server("127.0.0.1", port)
app.run()
