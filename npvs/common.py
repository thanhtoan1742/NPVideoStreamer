import logging


def log(message: str, header: str = "") -> None:
    print("-" * 60)
    if header != "":
        print(header)
        print("-" * 40)
    print(message)
    print("-" * 60)


def split(s: str, delim: str) -> list[str]:
    assert len(delim) == 1
    return list(map(lambda x: x.strip(), s.strip(delim).split(delim)))


def get_logger(name: str) -> logging.Logger:
    formatter = logging.Formatter(
        fmt="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d:%H:%M:%S",
    )

    handler = logging.FileHandler(name + ".log", "w")
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    return logger
