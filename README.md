# NP Video streamer

## Implementation

This implementation split video frame data then send over TCP connection.

## How to run

To install all dependencies, run:
```sh
pip install -r requirements.txt
```

To launch server, run:
```sh
python Server.py rtspPort
```

To launch server, run:
```sh
python Client.py serverIP serverRtspPort
```

Server's RTSP port should be empty (for example, you can chose 1200).
