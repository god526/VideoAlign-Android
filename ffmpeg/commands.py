"""Build FFmpeg filter graphs for export.

The filter graph uses the same linear sync mapping as the editor. Overlay
video ``B`` is delayed onto the main timeline with ``setpts``, scaled to the
configured size, and drawn at the configured position.
"""

from __future__ import annotations

from core.sync import mapping_from_points
from models.overlay import OverlayClip
from models.sync_point import SyncPoint
from models.video import VideoSource


def build_ffmpeg_command(
    main_video: VideoSource,
    overlay: OverlayClip,
    sync_points: list[SyncPoint],
    output_path: str,
    *,
    output_width: int | None = None,
    output_height: int | None = None,
    fps: float | None = None,
) -> list[str]:
    """Return a complete ``ffmpeg`` argv list for one overlay."""
    effective_points = sync_points or [SyncPoint(overlay.timeline_start, 0.0)]
    mapping = mapping_from_points(effective_points)
    k = mapping.k
    b = mapping.b

    # Preview uses:
    #   overlay_time = k * main_time + b
    # Therefore:
    #   main_time = overlay_time / k - b / k
    if abs(k) < 1e-9:
        setpts_expr = "PTS-STARTPTS"
    else:
        delay = -(b / k)
        setpts_expr = f"(PTS-STARTPTS)/{k:.9f}/TB+{delay:.9f}/TB"

    scale_filter = f"scale={overlay.transform.width}:{overlay.transform.height}"
    chain = f"[1:v]setpts={setpts_expr},{scale_filter}[ov]"
    final_parts = [f"[0:v][ov]overlay={overlay.transform.x}:{overlay.transform.y}"]
    if output_width and output_height:
        final_parts.append(f"scale={output_width}:{output_height}")
    if fps:
        final_parts.append(f"fps={fps:.6f}")
    final = ",".join(final_parts) + "[vout]"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        main_video.path,
        "-i",
        overlay.source.path,
        "-filter_complex",
        f"{chain};{final}",
        "-map",
        "[vout]",
        "-map",
        "0:a?",
    ]

    command.extend(["-c:v", "libx264", "-preset", "medium", "-crf", "18"])
    command.append(output_path)
    return command


def build_export_plan(
    main_video: VideoSource,
    overlay: OverlayClip,
    sync_points: list[SyncPoint],
    output_path: str,
) -> dict:
    """Return both the command and a human-readable plan."""
    command = build_ffmpeg_command(main_video, overlay, sync_points, output_path)
    mapping = mapping_from_points(sync_points)
    return {
        "command": command,
        "sync": {
            "speed_ratio": mapping.k,
            "offset": mapping.b,
        },
        "overlay_start": overlay.timeline_start,
        "transform": {
            "x": overlay.transform.x,
            "y": overlay.transform.y,
            "width": overlay.transform.width,
            "height": overlay.transform.height,
        },
    }
