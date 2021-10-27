from common import *


RTSP_MESSAGE_SIZE = 1 << 10

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


def createRequest(request: dict) -> str:
    """
    method, filName, CSeq fields are required for all method.
    Some methods may required additional fields.
    Attributes: method, fileName, CSeq, session, clientPort.
    """
    message = f"{request['method']} {request['fileName']} RTSP/1.0\n"
    message += f"CSeq: {request['CSeq']}\n"

    if "session" in request:
        message += f"session: {request['session']}\n"

    if "clientPort" in request:
        message += f"transport: RTP/UDP; clientPort={request['clientPort']};\n"

    return message.strip()


def parseRequest(message: str) -> dict:
    request = {}
    lines = message.split('\n')

    # format example
    # SETUP a.mp4 RTSP/1.0
    line = lines[0].split()
    request["method"] = line[0]
    request["fileName"] = line[1]

    # format example
    # CSeq: 12
    line = split(lines[1], ":")
    request["CSeq"] = int(line[1])


    # format example
    # transport: RTP/UDP; clientPort=1200;
    # session: 10
    for i in range(2, len(lines)):
        field, content = split(lines[i], ":")
        if field == "session":
            request["session"] = int(content)
        if field == "transport":
            attribtues = split(content, ";")
            for att in attribtues:
                if not "=" in att:
                    continue
                key, value = split(att, "=")
                if key in ["clientPort", "serverPort"]:
                    request[key] = int(value)
                else:
                    request[key] = value

    return request


def createRespond(respond: dict) -> str:
    """
    statusCode fields are required.
    Attributes: statusCode, CSeq, session, clientPort, serverPort.
    """
    message = f"RTSP/1.0 {respond['statusCode']} {StatusCode.DESCRIPTION[respond['statusCode']]}\n"
    message += f"CSeq: {respond['CSeq']}\n"

    if "session" in respond:
        message += f"session: {respond['session']}\n"

    if ("clientPort" in respond) or ("serverPort" in respond):
        message += f"transport: RTP/UDP;"
        if "clientPort" in respond:
            message += f" clientPort={respond['clientPort']};"
        if "serverPort" in respond:
            message += f" serverPort={respond['serverPort']};"
        message += "\n"

    return message.strip()


def parseRespond(message: str) -> dict:
    respond = {}
    lines = message.split('\n')

    # format example
    # RTSP/1.0 200 OK
    line = lines[0].split()
    respond["statusCode"] = int(line[1])

    # format example
    # CSeq: 10
    line = split(lines[1], ":")
    respond["CSeq"] = int(line[1])

    # format example
    # transport: RTP/UDP; clientPort=1200, serverPort=1020;
    # session: 10
    for i in range(2, len(lines)):
        field, content = split(lines[i], ":")
        if field == "session":
            respond["session"] = int(content)
        if field == "transport":
            attribtues = split(content, ";")
            for att in attribtues:
                if not "=" in att:
                    continue
                key, value = split(att, "=")
                if key in ["clientPort", "serverPort"]:
                    respond[key] = int(value)
                else:
                    respond[key] = value

    return respond
