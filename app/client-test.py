import socket

import cv2
import numpy as np
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image

from npvs.ps_receiver import PsReceiver

IP = "127.0.0.1"
PORT = 1201
BUFFER_SIZE = 1 << 14


def toTexture(image: np.ndarray) -> Texture:
    buffer = cv2.flip(image, 0).tostring()
    texture = Texture.create(size=(image.shape[1], image.shape[0]), colorfmt="bgr")
    texture.blit_buffer(buffer, colorfmt="bgr", bufferfmt="ubyte")
    return texture


class ClientApp(App):
    def build(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((IP, PORT))
        self.ps

        self.fps = 60
        self.playing = False

        layout = BoxLayout(orientation="vertical")

        self.image = Image(size_hint_y=4 / 5)
        layout.add_widget(self.image)
        buttons = BoxLayout(size_hint_y=1 / 5)
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

        Clock.schedule_interval(self.update, 1 / self.fps)
        return layout

    def on_stop(self, *args):
        self.client.close()
        return True

    def setup_callback(self, button):
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

        ok, frame = self.client.next_frame()
        if not ok:
            self.logger.info("missed frame")
            return

        self.logger.info("got frame")
        self.image.texture = toTexture(frame)
