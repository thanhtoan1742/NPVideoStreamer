import socket

IP = "127.0.0.1"
PORT = 41183
BUFFER_SIZE = 1 << 14

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((IP, PORT))

size = 0
while True:
    data = client.recv(BUFFER_SIZE)
    if not data:
        break
    size += len(data)
print("total:", size)
