"""High-level export service."""

from __future__ import annotations

from ffmpeg.commands import build_ffmpeg_command
from ffmpeg.runner import run_ffmpeg
from models.overlay import OverlayClip
from models.sync_point import SyncPoint
from models.video import VideoSource


def export_overlay_video(
    main_video: VideoSource,
    overlay: OverlayClip,
    sync_points: list[SyncPoint],
    output_path: str,
    on_progress=None,
) -> int:
    """Export the composited video and return the process exit code."""
    command = build_ffmpeg_command(
        main_video,
        overlay,
        sync_points,
        output_path,
    )
    result = run_ffmpeg(command, on_progress=on_progress)
    return result
