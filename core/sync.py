"""Time synchronisation between the main timeline and an overlay.

The model used here is the linear mapping::

    overlay_time = k * main_time + b

With one point only ``k`` is 1.0 (both videos run at the same speed), so the
mapping reduces to a fixed offset. With two points the mapping can also express
different playback speeds.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.sync_point import SyncPoint


@dataclass
class SyncMapping:
    k: float = 1.0
    b: float = 0.0

    def overlay_time(self, main_time: float) -> float:
        return self.k * main_time + self.b

    def main_time(self, overlay_time: float) -> float:
        if self.k == 0:
            return 0.0
        return (overlay_time - self.b) / self.k

    @property
    def is_identity(self) -> bool:
        return abs(self.k - 1.0) < 1e-9 and abs(self.b) < 1e-9


def mapping_from_points(points: list[SyncPoint]) -> SyncMapping:
    """Build a linear mapping from one or two sync points."""
    if not points:
        return SyncMapping()

    first = points[0]
    if len(points) == 1:
        return SyncMapping(k=1.0, b=first.overlay_time - first.main_time)

    a, b_pt = points[0], points[1]
    delta_main = b_pt.main_time - a.main_time
    if abs(delta_main) < 1e-9:
        return SyncMapping(k=1.0, b=a.overlay_time - a.main_time)

    k = (b_pt.overlay_time - a.overlay_time) / delta_main
    b = a.overlay_time - k * a.main_time
    return SyncMapping(k=k, b=b)


def overlay_timeline_start(mapping: SyncMapping, main_time: float) -> float:
    """Convenience wrapper returning the overlay time at a main time."""
    return mapping.overlay_time(main_time)
