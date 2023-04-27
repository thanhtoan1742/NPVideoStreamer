import socket
from threading import Thread

from npvs.common import *
from npvs.server_worker import ServerWorker


class Server:
    """
    Listen to incomming connection from clients.
    For each client, create new worker to serve that client.
    """

    def __init__(self, ip: str, port: int) -> None:
        self.logger = get_logger("server")
        self.ip = ip
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.ip, self.port))
        self.socket.listen(5)

    def __del__(self) -> None:
        self.socket.close()

    def run(self) -> None:
        # TODO: add proper termination mechanism
        workers = []
        while True:
            client_socket, (client_ip, client_port) = self.socket.accept()
            self.logger.info("Accepted connection (%s, %s)", client_ip, client_port)

            worker = ServerWorker(client_socket, client_ip, client_port)
            workers.append(worker)
            Thread(target=worker.run).start()
