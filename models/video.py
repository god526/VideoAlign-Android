"""Video source metadata model."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class VideoSource:
    """Metadata describing a video file.

    ``path`` is the only field the user supplies. The remaining fields are
    populated by :mod:`video.metadata` after probing the file.
    """

    path: str
    width: int = 0
    height: int = 0
    fps: float = 0.0
    frame_count: int = 0
    duration: float = 0.0
    has_audio: bool = False
    codec: str = ""
    metadata: dict = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        return Path(self.path).name

    @property
    def resolution(self) -> tuple[int, int]:
        return self.width, self.height

    @property
    def aspect_ratio(self) -> float:
        if self.width and self.height:
            return self.width / self.height
        return 16.0 / 9.0
