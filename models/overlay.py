"""Overlay transform and clip models."""

from __future__ import annotations

from dataclasses import dataclass, field

from models.video import VideoSource


@dataclass
class OverlayTransform:
    """Position and size of an overlay in *main video* pixels."""

    x: int = 0
    y: int = 0
    width: int = 320
    height: int = 180

    def clamp_to(self, main_width: int, main_height: int) -> None:
        self.width = max(1, int(self.width))
        self.height = max(1, int(self.height))
        self.x = max(0, min(int(self.x), main_width - self.width))
        self.y = max(0, min(int(self.y), main_height - self.height))


@dataclass
class OverlayClip:
    """An overlay video with transform, timeline range and sync mapping."""

    source: VideoSource
    transform: OverlayTransform = field(default_factory=OverlayTransform)
    timeline_start: float = 0.0
    timeline_end: float | None = None
    muted: bool = False
    visible: bool = True

    @property
    def name(self) -> str:
        return self.source.display_name
