from sys import getsizeof as sizeof

SOCKET_BUFFER_SIZE = 65500

def log(message: str, header: str = "") -> None:
    print("-"*60)
    if header != "":
        print(header)
        print("-"*40)
    print(message)
    print("-"*60)


def split(s: str, delim: str) -> list[str]:
    assert len(delim) == 1
    return list(map(lambda x: x.strip(), s.strip(delim).split(delim)))
