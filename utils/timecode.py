"""Timecode helpers.

VideoAlign stores all time values as float seconds internally. The UI displays
and accepts ``HH:MM:SS.mmm`` strings, and the conversion happens only here so
the rest of the application never has to guess about units.
"""

from __future__ import annotations


def format_tc(seconds: float) -> str:
    """Format seconds as ``HH:MM:SS.mmm``."""
    seconds = max(0.0, float(seconds))
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def parse_tc(text: str) -> float:
    """Parse a timecode string into float seconds.

    Accepted forms include ``30``, ``1:30``, ``01:30.500`` and
    ``01:02:03.250``. A plain number is always interpreted as seconds.
    """
    text = str(text).strip().replace(",", ".")
    if not text:
        return 0.0

    parts = text.split(":")
    if len(parts) > 3:
        raise ValueError(f"Invalid timecode: {text!r}")

    values = []
    for part in parts:
        values.append(float(part))

    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return values[0] * 60 + values[1]
    return values[0] * 3600 + values[1] * 60 + values[2]


def clamp(value: float, low: float, high: float) -> float:
    """Return ``value`` clamped to the inclusive ``[low, high]`` range."""
    return max(low, min(high, value))
