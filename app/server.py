import multiprocessing as mp
import sys

from npvs.server import Server

if __name__ == "__main__":
    mp.set_start_method("spawn")
    try:
        port = int(sys.argv[1])
    except:
        print("Usage: python Server.py rtspPort\n")

    app = Server("", port)
    app.run()
