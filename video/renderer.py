"""Preview compositor.

This is deliberately separated from the GUI. It takes a project and a main
timeline timestamp, reads the required frames and returns a BGR NumPy image
that is ready to be displayed in the preview canvas.
"""

from __future__ import annotations

import cv2
import numpy as np

from core.timeline import overlay_time_for_clip
from models.overlay import OverlayClip
from models.video import VideoSource
from video.decoder import VideoReader


class Compositor:
    def __init__(self, main_video: VideoSource | None = None):
        self.main_reader: VideoReader | None = None
        self.overlay_readers: dict[str, VideoReader] = {}
        if main_video:
            self.set_main_video(main_video)

    def set_main_video(self, source: VideoSource) -> None:
        self.close_main()
        self.main_reader = VideoReader(source.path)

    def set_overlay(self, overlay: OverlayClip) -> None:
        self.close_overlay(overlay)
        self.overlay_readers[overlay.name] = VideoReader(overlay.source.path)

    def close_main(self) -> None:
        if self.main_reader:
            self.main_reader.close()
            self.main_reader = None

    def close_overlay(self, overlay: OverlayClip) -> None:
        reader = self.overlay_readers.pop(overlay.name, None)
        if reader:
            reader.close()

    def close(self) -> None:
        self.close_main()
        for reader in self.overlay_readers.values():
            reader.close()
        self.overlay_readers.clear()

    def render(
        self,
        main_time: float,
        overlays: list[OverlayClip],
        sync_points: list,
    ) -> np.ndarray | None:
        if not self.main_reader:
            return None

        main_frame = self.main_reader.frame_at(main_time)
        if main_frame is None:
            return None

        canvas = main_frame.copy()
        for overlay in overlays:
            if not overlay.visible:
                continue
            overlay_time = overlay_time_for_clip(overlay, main_time, sync_points)
            if overlay_time is None:
                continue

            reader = self.overlay_readers.get(overlay.name)
            if reader is None:
                reader = VideoReader(overlay.source.path)
                self.overlay_readers[overlay.name] = reader

            overlay_frame = reader.frame_at(overlay_time)
            if overlay_frame is None:
                continue

            w, h = overlay.transform.width, overlay.transform.height
            w = max(1, int(w))
            h = max(1, int(h))
            scaled = cv2.resize(overlay_frame, (w, h), interpolation=cv2.INTER_AREA)
            _overlay_frame(canvas, scaled, overlay.transform.x, overlay.transform.y)

        return canvas


def _overlay_frame(canvas: np.ndarray, overlay: np.ndarray, x: int, y: int) -> None:
    h, w = overlay.shape[:2]
    ch = canvas.shape[0]
    cw = canvas.shape[1]
    if x >= cw or y >= ch or x + w <= 0 or y + h <= 0:
        return

    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(cw, x + w)
    y1 = min(ch, y + h)
    ox0 = x0 - x
    oy0 = y0 - y
    ox1 = x1 - x
    oy1 = y1 - y

    roi = canvas[y0:y1, x0:x1]
    patch = overlay[oy0:oy1, ox0:ox1]
    if patch.shape[:2] != roi.shape[:2]:
        return
    canvas[y0:y1, x0:x1] = patch
