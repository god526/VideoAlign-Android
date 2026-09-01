"""Timeline calculations shared by the UI and exporter."""

from __future__ import annotations

from core.sync import mapping_from_points
from models.overlay import OverlayClip
from models.sync_point import SyncPoint


def project_duration(main_duration: float, overlays: list[OverlayClip]) -> float:
    """Return the longest duration across the main video and overlay clips."""
    duration = max(0.0, main_duration)
    for overlay in overlays:
        end = overlay.timeline_end or overlay.source.duration or 0.0
        duration = max(duration, overlay.timeline_start + end)
    return duration


def overlay_time_for_clip(
    clip: OverlayClip,
    main_time: float,
    sync_points: list,
) -> float | None:
    """Map ``main_time`` to overlay time for a clip.

    Returns ``None`` when the overlay should not be visible at this moment.
    """
    if main_time < clip.timeline_start:
        return None
    if clip.timeline_end is not None and main_time > clip.timeline_end:
        return None

    effective_points = sync_points or [SyncPoint(clip.timeline_start, 0.0)]
    mapping = mapping_from_points(effective_points)
    overlay_time = mapping.overlay_time(main_time)
    source_duration = clip.source.duration
    if source_duration and overlay_time > source_duration:
        return None
    return max(0.0, overlay_time)
