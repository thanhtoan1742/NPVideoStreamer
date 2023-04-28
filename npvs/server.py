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
        self.socket.listen(1)

        self.worker_threads = []

    def __del__(self) -> None:
        self.socket.close()
        for thread in self.worker_threads:
            thread.join()

    def run(self) -> None:
        # TODO: add proper termination mechanism
        while True:
            client_socket, (client_ip, client_port) = self.socket.accept()
            self.logger.info("Accepted connection (%s, %s)", client_ip, client_port)

            worker = ServerWorker(client_socket, client_ip, client_port)
            thread = Thread(target=worker.run)
            thread.start()
            self.worker_threads.append(thread)
            break
