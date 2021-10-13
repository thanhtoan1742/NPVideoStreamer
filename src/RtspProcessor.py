from enum import Enum

class Method(Enum):
    SETUP = "SETUP"
    PLAY = "PLAY"
    PAUSE = "PAUSE"
    TEARDOWN = "TEARDOWN "

class StatusCode(Enum):
    OK = 200
    FILE_NOT_FOUND = 404
    CONNECTION_ERROR = 500

    DESCRIPTION = {
        OK: "OK",
        FILE_NOT_FOUND: "FILE_NOT_FOUND",
        CONNECTION_ERROR: "CONNECTION_ERROR" 
    }