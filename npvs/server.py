import socket
from multiprocessing import Process

from npvs.common import *
from npvs.server_worker import run_server_worker


class Server:
    """
    Listen to incomming connection from clients.
    For each client, create new worker to serve that client.
    """

    def __init__(self, ip: str, port: int) -> None:
        self.logger = get_logger("server")
        self.ip = ip
        self.port = port
        self.worker_process = []

    def __del__(self) -> None:
        self.logger.info("Shuting down server")
        self.socket.close()
        for thread in self.worker_process:
            thread.join()

    def run(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.ip, self.port))
        s.listen(1)
        self.logger.info(
            "Server listening for incomming connections on (%s, %d)", self.ip, self.port
        )
        # TODO: add proper termination mechanism
        while True:
            client_socket, (client_ip, client_port) = s.accept()
            self.logger.info("Accepted connection (%s, %s)", client_ip, client_port)
            print("Accepted connection", client_ip, client_port)

            process = Process(
                target=run_server_worker, args=[client_socket, client_ip, client_port]
            )
            process.start()
            self.worker_process.append(process)
            break
        s.close()
