# NP Video streamer

## Implementation

This implementation split video frame data then send over TCP connection.

## Dependencies
To install all dependencies, run:
```sh
pip install -r requirements.txt
```

## Application

To launch server, from the project base directory, set the python
path to includes the project then run:
```sh
PYTHONPATH="." python app/server.py <rtsp_port>
```

Similar to launching server, run:
```sh
PYTHONPATH="." python app/client.py <server_ip> <server_rtsp_port> <filename>
```

Server's RTSP port should be empty (for example, you can chose 1200).

## Testing
To run test, from the project base directory, set the python
path to includes the project then run:
```sh
PYTHONPATH="." python -m unittest discover -s "tests/"
```