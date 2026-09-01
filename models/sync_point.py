"""Synchronisation point model."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SyncPoint:
    """Maps one main-video time to one overlay-video time."""

    main_time: float
    overlay_time: float

    def as_dict(self) -> dict[str, float]:
        return {"main": self.main_time, "overlay": self.overlay_time}

    @classmethod
    def from_dict(cls, data: dict[str, float]) -> "SyncPoint":
        return cls(main_time=float(data["main"]), overlay_time=float(data["overlay"]))
