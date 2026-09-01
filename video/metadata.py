"""Video probing helpers built on OpenCV.

OpenCV is already available in this environment and provides reliable frame
decoding for preview. The exporter still targets FFmpeg, so these values are
only used for the editor and are not written directly into the final command.
"""

from __future__ import annotations

import cv2

from models.video import VideoSource
from utils.logger import get_logger

logger = get_logger(__name__)


def probe_video(path: str) -> VideoSource:
    """Return populated :class:`VideoSource` metadata for ``path``."""
    source = VideoSource(path=str(path))
    cap = cv2.VideoCapture(source.path)
    if not cap.isOpened():
        cap.release()
        raise IOError(f"无法打开视频文件: {source.path}")

    try:
        source.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        source.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        source.fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
        source.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        source.codec = _fourcc_to_string(cap.get(cv2.CAP_PROP_FOURCC))
        if source.fps > 0 and source.frame_count > 0:
            source.duration = source.frame_count / source.fps
        else:
            source.duration = 0.0
    finally:
        cap.release()

    if source.duration <= 0 and source.frame_count:
        source.duration = source.frame_count / max(source.fps, 0.001)

    logger.info(
        "Probed %s: %dx%d %.3ffps %s frames %.3fs",
        source.display_name,
        source.width,
        source.height,
        source.fps,
        source.frame_count,
        source.duration,
    )
    return source


def _fourcc_to_string(fourcc: float) -> str:
    if not fourcc:
        return ""
    value = int(fourcc)
    chars = [
        chr((value >> shift) & 0xFF)
        for shift in (0, 8, 16, 24)
    ]
    return "".join(c for c in chars if c.isprintable())
