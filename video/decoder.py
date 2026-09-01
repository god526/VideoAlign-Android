"""Frame decoding wrapper around OpenCV."""

from __future__ import annotations

import cv2
import numpy as np

from models.video import VideoSource
from video.metadata import probe_video


class VideoReader:
    """A small seekable frame reader for one video file."""

    def __init__(self, path: str):
        self.path = str(path)
        self.source: VideoSource = probe_video(self.path)
        self._cap = cv2.VideoCapture(self.path)
        if not self._cap.isOpened():
            raise IOError(f"无法打开视频文件: {self.path}")

    def close(self) -> None:
        if getattr(self, "_cap", None) is not None:
            self._cap.release()

    def __enter__(self) -> "VideoReader":
        return self

    def __exit__(self, *_exc_info) -> None:
        self.close()

    def seek(self, seconds: float) -> None:
        """Move the capture position to the requested timestamp."""
        seconds = max(0.0, float(seconds))
        self._cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000.0)

    def read_frame(self) -> np.ndarray | None:
        ok, frame = self._cap.read()
        if not ok or frame is None:
            return None
        return frame

    def frame_at(self, seconds: float) -> np.ndarray | None:
        """Seek to ``seconds`` and return the next decoded BGR frame."""
        self.seek(seconds)
        return self.read_frame()

    def frame_at_index(self, index: int) -> np.ndarray | None:
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, int(index))
        return self.read_frame()
