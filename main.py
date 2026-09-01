"""VideoAlign — Android / desktop entry point (Kivy UI)."""

from __future__ import annotations

import os

os.environ.setdefault("KIVY_NO_ARGS", "1")

from kivy.app import App  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.lang import Builder  # noqa: E402

from app_kivy.controller import VideoAlignController  # noqa: E402
from app_kivy.screen import MainScreen  # noqa: E402

# 布局文件与 App 类名不同，需要显式加载
Builder.load_file(os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.kv"))


class VideoAlignApp(App):
    title = "VideoAlign"

    def build(self):
        self.controller = VideoAlignController()
        Window.clearcolor = (0.08, 0.11, 0.13, 1)
        return MainScreen(controller=self.controller)

    def on_pause(self):
        # Android: stop playback while the app is backgrounded.
        self.controller.on_pause()
        return True


def run() -> None:
    VideoAlignApp().run()


if __name__ == "__main__":
    run()
