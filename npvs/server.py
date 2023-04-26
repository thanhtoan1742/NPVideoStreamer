import socket
from threading import Thread

from npvs.common import *
from npvs.server_worker import ServerWorker


class Server:
    def __init__(self, ip: str, port: int) -> None:
        self.ip = ip
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        self.socket.listen(5)

    def __del__(self) -> None:
        self.socket.close()

    def run(self) -> None:
        # Receive client info (address,port) through RTSP/TCP session
        workers = []
        while True:
            client_socket, (client_ip, client_port) = self.socket.accept()

            worker = ServerWorker(client_socket, client_ip, client_port)
            workers.append(worker)
            Thread(target=worker.run).start()
