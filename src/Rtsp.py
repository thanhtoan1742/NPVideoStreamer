from random import randint
from common import *

class Method:
    SETUP = "SETUP"
    PLAY = "PLAY"
    PAUSE = "PAUSE"
    TEARDOWN = "TEARDOWN"

class StatusCode:
    OK = 200
    FILE_NOT_FOUND = 404
    CONNECTION_ERROR = 500

    DESCRIPTION = {
        OK: "OK",
        FILE_NOT_FOUND: "FILE_NOT_FOUND",
        CONNECTION_ERROR: "CONNECTION_ERROR"
    }

def createRequest(method: Method, CSeq: int, fileName: str, session: int = -1, rtpPort: int = -1) -> str:
    message = f"{method} {fileName} RTSP/1.0\n"
    message += f"CSeq: {CSeq}\n"
    if rtpPort != -1:
        message += f"Transport: RTP/UDP; client_port={rtpPort}\n"
    if session != -1:
        message += f"Session: {session}\n"

    return message.strip()

def parseRequest(message: str) -> dict:
    request = {}

    lines = message.split('\n')
    line = lines[0].split()
    request["method"] = line[0]
    request["fileName"] = line[1]

    line = lines[1].split(":")
    request["CSeq"] = int(line[1])

    if request["method"] == Method.SETUP:
        line = lines[2].split("=")
        request["rtpPort"] = int(line[1])
    else:
        if len(lines) > 2:
            line = lines[2].split(":")
            request["session"] = int(line[1])

    return request


def createRespond(statusCode: StatusCode, CSeq: int, session: int = -1, serverPort = 0, clientPort = 0) -> str:
    message = f"RTSP/1.0 {statusCode} {StatusCode.DESCRIPTION[statusCode]}\n"
    message += f"CSeq: {CSeq}\n"
    if session != -1:
        message += f"Session: {session}\n"

    if serverPort <= 0 and clientPort <= 0:
        return message.strip()

    message += f"Transport: RTP/UDP;"
    if clientPort > 0:
        message += f" clientPort={clientPort};"
    if serverPort > 0:
        message += f" serverPort={serverPort};"
    message += "\n"

    return message.strip()


def parseRespond(message: str) -> dict:
    respond = {}

    lines = message.split('\n')
    line = lines[0].split()
    respond["statusCode"] = int(line[1])

    line = lines[1].split(":")
    respond["CSeq"] = int(line[1])

    if len(lines) > 2:
        line = lines[2].split(":")
        respond["session"] = int(line[1])

    if len(lines) > 3:
        line = lines[3].split(";")
        if len(line) > 1:
            key, value = line[1].split("=")
            respond[key.strip()] = int(value)
        if len(line) > 2:
            key, value = line[2].split("=")
            respond[key.strip()] = int(value)


    return respond