"""Preview canvas widget.

Shows the composited frame (main video + overlay) as a Kivy texture and lets
the user drag the overlay box around with touch gestures.
"""

from __future__ import annotations

import cv2
import numpy as np
from kivy.core.image import Texture
from kivy.graphics import Color, Line, Rectangle
from kivy.uix.widget import Widget


class PreviewWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.controller = None
        self._texture = None
        self._frame_w = 0
        self._frame_h = 0
        self._scale = 1.0
        self._ox = 0.0  # display offset of the video rectangle
        self._oy = 0.0
        self._dragging = False
        self._grab = (0, 0)  # grab offset inside the overlay, in video pixels

        with self.canvas:
            Color(1, 1, 1, 1)
            self._img = Rectangle(pos=(0, 0), size=(0, 0))
            Color(0.3, 0.75, 1.0, 1.0)
            self._border = Line(rectangle=(0, 0, 0, 0), width=2)

        self.bind(pos=self._layout, size=self._layout)

    # ------------------------------------------------------------------
    # Frame display
    # ------------------------------------------------------------------

    def bind_controller(self, controller) -> None:
        self.controller = controller

    def set_frame(self, frame: np.ndarray) -> None:
        h, w = frame.shape[:2]
        if self._texture is None or self._frame_w != w or self._frame_h != h:
            self._texture = Texture.create(size=(w, h), colorfmt="rgb")
            self._frame_w, self._frame_h = w, h
        # OpenCV gives BGR with the origin at top-left; Kivy textures are RGB
        # with the origin at bottom-left, so flip vertically.
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = np.ascontiguousarray(rgb[::-1])
        self._texture.blit_buffer(rgb.tobytes(), colorfmt="rgb", bufferfmt="ubyte")
        self._img.texture = self._texture
        self._layout()

    def _layout(self, *_args) -> None:
        if self._texture is None or self._frame_w <= 0:
            return
        avail_w, avail_h = self.width, self.height
        if avail_w <= 0 or avail_h <= 0:
            return
        self._scale = min(avail_w / self._frame_w, avail_h / self._frame_h)
        disp_w = self._frame_w * self._scale
        disp_h = self._frame_h * self._scale
        self._ox = self.x + (avail_w - disp_w) / 2.0
        self._oy = self.y + (avail_h - disp_h) / 2.0
        self._img.pos = (self._ox, self._oy)
        self._img.size = (disp_w, disp_h)
        self._update_border()

    def _update_border(self) -> None:
        if self._frame_w <= 0:
            self._border.rectangle = (0, 0, 0, 0)
            return
        ov = self._overlay()
        if ov is None:
            self._border.rectangle = (0, 0, 0, 0)
            return
        t = ov.transform
        x = self._ox + t.x * self._scale
        y = self._oy + (self._frame_h - t.y - t.height) * self._scale
        w = t.width * self._scale
        h = t.height * self._scale
        self._border.rectangle = (x, y, w, h)

    # ------------------------------------------------------------------
    # Touch: drag the overlay box
    # ------------------------------------------------------------------

    def _overlay(self):
        if self.controller and self.controller.overlays:
            return self.controller.overlays[0]
        return None

    def _to_video(self, tx: float, ty: float):
        """Map widget coordinates to video pixels (or None if outside)."""
        if self._frame_w <= 0 or self._scale <= 0:
            return None
        vx = (tx - self._ox) / self._scale
        vy = (self._oy + self._frame_h * self._scale - ty) / self._scale
        if 0 <= vx < self._frame_w and 0 <= vy < self._frame_h:
            return vx, vy
        return None

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        ov = self._overlay()
        if ov is None:
            return super().on_touch_down(touch)
        vp = self._to_video(*touch.pos)
        if vp is None:
            return super().on_touch_down(touch)
        vx, vy = vp
        t = ov.transform
        if t.x <= vx <= t.x + t.width and t.y <= vy <= t.y + t.height:
            self._dragging = True
            self._grab = (vx - t.x, vy - t.y)
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._dragging and touch.grab_current is self:
            ov = self._overlay()
            vp = self._to_video(*touch.pos)
            if ov is not None and vp is not None:
                t = ov.transform
                t.x = int(vp[0] - self._grab[0])
                t.y = int(vp[1] - self._grab[1])
                if self.controller and self.controller.main_video:
                    t.clamp_to(
                        self.controller.main_video.width,
                        self.controller.main_video.height,
                    )
                self._update_border()
                if self.controller:
                    self.controller._request_render()
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._dragging and touch.grab_current is self:
            self._dragging = False
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)
