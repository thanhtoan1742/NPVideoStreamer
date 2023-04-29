import logging


def split(s: str, delim: str) -> list[str]:
    assert len(delim) == 1
    return list(map(lambda x: x.strip(), s.strip(delim).split(delim)))


requested_logger = {}


def get_logger(name: str) -> logging.Logger:
    global requested_logger
    if name in requested_logger:
        return requested_logger[name]

    formatter = logging.Formatter(
        fmt="%(asctime)s,%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d:%H:%M:%S",
    )

    if name == "null":
        handler = logging.NullHandler
        logger = logging.getLogger(name)
        logger.addHandler(handler)
    else:
        file_handler = logging.FileHandler(name + ".log", "w")
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()

        logger = logging.getLogger(name)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
        logger.setLevel(logging.INFO)

    requested_logger[name] = logger
    return logger
