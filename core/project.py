"""Project container and JSON persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from models.overlay import OverlayClip, OverlayTransform
from models.sync_point import SyncPoint
from models.video import VideoSource


PROJECT_VERSION = "1.0"


@dataclass
class Project:
    main_video: VideoSource | None = None
    overlays: list[OverlayClip] = field(default_factory=list)
    sync_points: list[SyncPoint] = field(default_factory=list)
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "version": PROJECT_VERSION,
            "main_video": None,
            "overlays": [],
            "sync_points": [point.as_dict() for point in self.sync_points],
        }
        if self.main_video:
            data["main_video"] = {
                "path": self.main_video.path,
            }
        for overlay in self.overlays:
            data["overlays"].append(
                {
                    "path": overlay.source.path,
                    "transform": asdict(overlay.transform),
                    "timeline_start": overlay.timeline_start,
                    "timeline_end": overlay.timeline_end,
                    "muted": overlay.muted,
                    "visible": overlay.visible,
                }
            )
        return data

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        self.path = str(path)

    @classmethod
    def load(cls, path: str | Path) -> "Project":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("version") != PROJECT_VERSION:
            raise ValueError(f"Unsupported project version: {data.get('version')!r}")

        project = cls(path=str(path))
        if data.get("main_video"):
            project.main_video = VideoSource(path=data["main_video"]["path"])
        for item in data.get("overlays", []):
            transform_data = item.get("transform", {})
            transform = OverlayTransform(
                x=int(transform_data.get("x", 0)),
                y=int(transform_data.get("y", 0)),
                width=int(transform_data.get("width", 320)),
                height=int(transform_data.get("height", 180)),
            )
            overlay = OverlayClip(
                source=VideoSource(path=item["path"]),
                transform=transform,
                timeline_start=float(item.get("timeline_start", 0.0)),
                timeline_end=item.get("timeline_end"),
                muted=bool(item.get("muted", False)),
                visible=bool(item.get("visible", True)),
            )
            project.overlays.append(overlay)
        project.sync_points = [
            SyncPoint.from_dict(point) for point in data.get("sync_points", [])
        ]
        return project
