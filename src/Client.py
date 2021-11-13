import socket, sys
import numpy as np
import cv2
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics.texture import Texture

from common import *
from MediaPlayer import MediaPlayer
import Rtsp, Rtp
from Video import VideoAssembler


def toTexture(image: np.ndarray) -> Texture:
    buffer = cv2.flip(image, 0).tostring()
    texture = Texture.create(size=(image.shape[1], image.shape[0]), colorfmt="bgr")
    texture.blit_buffer(buffer, colorfmt="bgr", bufferfmt="ubyte")
    return texture


def toTextureGrey(image: np.ndarray) -> Texture:
    buffer = cv2.flip(image, 0).tostring()
    texture = Texture.create(size=(image.shape[1], image.shape[0]), colorfmt="luminance")
    texture.blit_buffer(buffer, colorfmt="luminance", bufferfmt="ubyte")
    return texture

class Client(MediaPlayer):
    def __init__(self, serverIp: str, serverRtspPort: int, fileName: str) -> None:
        super().__init__()

        self.serverIp = serverIp
        self.serverRtspPort = serverRtspPort
        self.fileName = fileName

        self.clientRtpPort = 0
        self.rtpSocket: socket.socket = None

        self.videoAssembler = VideoAssembler()

        self.initRtsp()


    def initRtsp(self) -> None:
        """Connect to the Server. Start a new RTSP/TCP session."""

        self.CSeq = 0
        self.session = -1

        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtspSocket.connect((self.serverIp, self.serverRtspPort))


    def __del__(self) -> None:
        self.teardown()
        self.rtspSocket.close()


    def sendRtspRequest(self, method: Rtsp.Method) -> bool:
        self.CSeq += 1

        request = {
            "method": method,
            "fileName": self.fileName,
            "CSeq": self.CSeq,
        }
        if method == Rtsp.Method.SETUP:
            request["clientPort"] = self.clientRtpPort
        else:
            request["session"] = self.session
        message = Rtsp.createRequest(request)
        self.rtspSocket.sendall(message.encode())

        message = self.rtspSocket.recv(Rtsp.RTSP_MESSAGE_SIZE).decode()
        self.respond = Rtsp.parseRespond(message)
        if self.respond["statusCode"] > 299:
            log(self.respond["statusCode"], "server responded")
            return False

        return True


    def _setup_(self) -> bool:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        self.clientRtpPort  = int(s.getsockname()[1]) # get the port
        s.listen()

        if not self.sendRtspRequest(Rtsp.Method.SETUP):
            self.rtpSocket.close()
            return False

        self.session = self.respond["session"]
        self.rtpSocket, _ = s.accept()
        self.rtpSocket.settimeout(0.5)

        return True

    def _play_(self) -> bool:
        return self.sendRtspRequest(Rtsp.Method.PLAY)

    def _pause_(self) -> bool:
        return self.sendRtspRequest(Rtsp.Method.PAUSE)

    def _teardown_(self) -> bool:
        if not self.sendRtspRequest(Rtsp.Method.TEARDOWN):
            return False
        self.rtpSocket.close()
        return True


    def _stream_(self) -> None:
        try:
            data = self.rtpSocket.recv(Rtp.PACKET_SIZE)
        except socket.timeout:
            print("timed out")
            return
        except:
            print("error in receiving data")
            return
        # print("received data")

        if not data:
            return

        self.videoAssembler.addPacket(Rtp.decode(data))



    def nextFrame(self):
        return self.videoAssembler.nextFrame()


class ClientApp(App):
    def build(self):
        self.client = Client(serverIp, rtspPort, fileName)
        self.fps = 60
        self.playing = False

        layout = BoxLayout(orientation="vertical")

        self.image = Image(size_hint_y=4/5)
        layout.add_widget(self.image)
        buttons = BoxLayout(size_hint_y=1/5)
        layout.add_widget(buttons)

        setup = Button(text="setup")
        setup.bind(on_press=self.setup_callback)
        buttons.add_widget(setup)

        play = Button(text="play")
        play.bind(on_press=self.play_callback)
        buttons.add_widget(play)

        pause = Button(text="pause")
        pause.bind(on_press=self.pause_callback)
        buttons.add_widget(pause)

        teardown = Button(text="teardown")
        teardown.bind(on_press=self.teardown_callback)
        buttons.add_widget(teardown)

        Clock.schedule_interval(self.update, 1/self.fps)
        return layout


    def on_stop(self, *args):
        self.client.teardown()
        return True


    def setup_callback(self, button):
        self.client.setup()
        self.playing = False


    def play_callback(self, button):
        self.client.play()
        self.playing = True


    def pause_callback(self, button):
        self.client.pause()
        self.playing = False


    def teardown_callback(self, button):
        self.client.teardown()
        self.playing = False


    def update(self, dt):
        if not self.playing:
            return

        ok, frame = self.client.nextFrame()
        if not ok:
            print("missed frame")
            return

        self.image.texture = toTexture(frame)


if __name__ == "__main__":
    try:
        serverIp = sys.argv[1]
        rtspPort = int(sys.argv[2])
        fileName = sys.argv[3]
    except:
        print("Usage: python Client.py serverIP serverRtspPort fileName\n")

    ClientApp().run()
