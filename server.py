import sys

from npvs.Server import Server

if __name__ == "__main__":
    try:
        rtspPort = int(sys.argv[1])
    except:
        print("Usage: python Server.py rtspPort\n")

    app = Server("", rtspPort)
    app.run()
