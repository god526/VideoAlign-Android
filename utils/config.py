"""Small application configuration container."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AppConfig:
    """Runtime configuration for the VideoAlign editor.

    The values in this first version are deliberately conservative so the
    preview stays responsive even on weaker Windows machines.
    """

    preview_max_width: int = 1280
    preview_max_height: int = 720
    playback_poll_ms: int = 16
    recent_project_path: str | None = None
    last_media_directory: str = ""
    project_extension: str = ".vap"
    metadata: dict = field(default_factory=dict)
