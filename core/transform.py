"""Coordinate mapping between the preview canvas and main-video pixels."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PreviewViewport:
    """Scale and offset used to map video pixels to canvas pixels."""

    video_width: int
    video_height: int
    canvas_width: int
    canvas_height: int
    scale: float = 1.0
    offset_x: int = 0
    offset_y: int = 0

    def __post_init__(self) -> None:
        self.recalculate()

    def recalculate(self) -> None:
        if self.video_width <= 0 or self.video_height <= 0:
            self.scale = 1.0
            self.offset_x = 0
            self.offset_y = 0
            return

        self.scale = min(
            self.canvas_width / self.video_width,
            self.canvas_height / self.video_height,
        )
        display_w = int(self.video_width * self.scale)
        display_h = int(self.video_height * self.scale)
        self.offset_x = (self.canvas_width - display_w) // 2
        self.offset_y = (self.canvas_height - display_h) // 2

    def video_to_canvas(self, x: float, y: float) -> tuple[int, int]:
        return (
            int(self.offset_x + x * self.scale),
            int(self.offset_y + y * self.scale),
        )

    def canvas_to_video(self, x: float, y: float) -> tuple[int, int]:
        return (
            int((x - self.offset_x) / self.scale),
            int((y - self.offset_y) / self.scale),
        )

    def size_to_canvas(self, width: float, height: float) -> tuple[int, int]:
        return int(width * self.scale), int(height * self.scale)
