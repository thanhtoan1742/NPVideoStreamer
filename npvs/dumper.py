class Dumper:
    def __init__(self, filename: str) -> None:
        self.filename = filename
        open(filename, "+w").close()
        self.fd = open(filename, "ab")

    def __del__(self) -> None:
        self.fd.close()

    def append(self, data: bytes) -> None:
        self.fd.write(data)
