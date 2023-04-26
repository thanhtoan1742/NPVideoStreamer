import sys

from npvs.server import Server

if __name__ == "__main__":
    try:
        port = int(sys.argv[1])
    except:
        print("Usage: python Server.py rtspPort\n")

    app = Server("", port)
    app.run()
