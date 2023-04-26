import sys

import cv2
import numpy as np
from kivy.app import App
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image

import npvs


def toTexture(image: np.ndarray) -> Texture:
    buffer = cv2.flip(image, 0).tostring()
    texture = Texture.create(size=(image.shape[1], image.shape[0]), colorfmt="bgr")
    texture.blit_buffer(buffer, colorfmt="bgr", bufferfmt="ubyte")
    return texture


def toTextureGrey(image: np.ndarray) -> Texture:
    buffer = cv2.flip(image, 0).tostring()
    texture = Texture.create(
        size=(image.shape[1], image.shape[0]), colorfmt="luminance"
    )
    texture.blit_buffer(buffer, colorfmt="luminance", bufferfmt="ubyte")
    return texture


class ClientApp(App):
    def build(self):
        self.client = npvs.Client(ip, rtspPort, fileName)
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
        ip = sys.argv[1]
        rtspPort = int(sys.argv[2])
        fileName = sys.argv[3]
    except:
        print("Usage: python Client.py serverIP serverRtspPort fileName\n")

    ClientApp().run()
