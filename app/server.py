import sys

from npvs.server import Server

try:
    port = int(sys.argv[1])
except:
    print("Usage: python Server.py rtspPort\n")

app = Server("", port)
app.run()
