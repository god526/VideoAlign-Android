"""UI-toolkit agnostic controller for the Kivy VideoAlign app.

Reuses the original project's pure-logic layers (models, core, video renderer)
and only adapts the scheduling (Kivy Clock) and file I/O (SAF on Android).
"""

from __future__ import annotations

import os
import threading

from kivy.clock import Clock

from app_kivy.file_picker import cache_dir, pick_save_location, pick_video, write_output
from core.playback import PlaybackEngine
from core.timeline import project_duration
from models.overlay import OverlayClip, OverlayTransform
from models.sync_point import SyncPoint
from models.video import VideoSource
from utils.timecode import format_tc
from video.metadata import probe_video
from video.renderer import Compositor


def _kivy_after(interval_ms: int, callback) -> object:
    """Adapter from Tkinter-style ``after`` to Kivy Clock."""
    return Clock.schedule_once(lambda _dt: callback(), interval_ms / 1000.0)


class VideoAlignController:
    """Holds project state and drives rendering. Talks to the UI through
    ``self.ui`` callbacks (set by the screen)."""

    def __init__(self):
        self.main_video: VideoSource | None = None
        self.overlays: list[OverlayClip] = []
        self.sync_points: list[SyncPoint] = []
        self.compositor = Compositor()
        self.playback = PlaybackEngine(after=_kivy_after, interval_ms=33)
        self.playback.on_tick = self._on_playback_tick

        self.ui = None  # set by MainScreen
        self._render_pending = False
        self.last_frame = None

    # ------------------------------------------------------------------
    # Media import
    # ------------------------------------------------------------------

    def import_main(self) -> None:
        pick_video(on_result=self._on_main_picked)

    def _on_main_picked(self, path: str | None) -> None:
        if not path:
            return
        try:
            source = probe_video(path)
        except Exception as exc:
            self._status(f"无法导入主视频: {exc}")
            return
        self.main_video = source
        self.overlays = []
        self.sync_points = []
        self.playback.stop()
        self.compositor.set_main_video(source)
        self._apply_state()
        self._status(f"主视频: {source.display_name} ({source.width}x{source.height})")

    def import_overlay(self) -> None:
        if not self.main_video:
            self._status("请先导入主视频")
            return
        pick_video(on_result=self._on_overlay_picked)

    def _on_overlay_picked(self, path: str | None) -> None:
        if not path:
            return
        try:
            source = probe_video(path)
        except Exception as exc:
            self._status(f"无法导入嵌入视频: {exc}")
            return

        width = max(1, self.main_video.width // 3)
        height = max(1, round(width / source.aspect_ratio))
        if height > self.main_video.height:
            height = max(1, self.main_video.height // 3)
            width = max(1, round(height * source.aspect_ratio))
        transform = OverlayTransform(
            x=max(0, self.main_video.width - width - 24),
            y=24,
            width=width,
            height=height,
        )
        overlay = OverlayClip(source=source, transform=transform, timeline_start=0.0)
        self.overlays.append(overlay)
        self.compositor.set_overlay(overlay)
        self._apply_state()
        self._status(f"嵌入视频: {source.display_name}（在预览区拖动蓝色框调整位置）")

    # ------------------------------------------------------------------
    # State / timeline
    # ------------------------------------------------------------------

    def _apply_state(self) -> None:
        duration = project_duration(
            self.main_video.duration if self.main_video else 0.0,
            self.overlays,
        )
        self.playback.set_duration(duration)
        if self.ui:
            self.ui.on_project_changed(self.main_video, self.overlays, self.sync_points, duration)

    def toggle_play(self) -> None:
        self.playback.toggle()
        if self.ui:
            self.ui.on_playing_changed(self.playback.playing)

    def seek(self, seconds: float) -> None:
        self.playback.seek(float(seconds))
        self._request_render()

    def step(self, direction: float) -> None:
        fps = self.main_video.fps if self.main_video else 30.0
        self.playback.seek(self.playback.current_time + direction / max(fps, 0.001))
        self._request_render()

    # ------------------------------------------------------------------
    # Sync points
    # ------------------------------------------------------------------

    def add_sync_point(self, main_time: float, overlay_time: float) -> None:
        self.sync_points.append(SyncPoint(main_time=float(main_time), overlay_time=float(overlay_time)))
        if self.ui:
            self.ui.on_sync_points_changed(self.sync_points)
        self._status(f"同步点 #{len(self.sync_points)}: 主={format_tc(main_time)} ⇄ 嵌入={format_tc(overlay_time)}")

    def remove_last_sync_point(self) -> None:
        if self.sync_points:
            self.sync_points.pop()
            if self.ui:
                self.ui.on_sync_points_changed(self.sync_points)
            self._status("已删除最后一个同步点")

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _on_playback_tick(self, _main_time: float) -> None:
        self._request_render()

    def _request_render(self) -> None:
        if self._render_pending:
            return
        self._render_pending = True
        Clock.schedule_once(self._do_render, 0)

    def render_frame(self, main_time: float):
        """Synchronously render one composited frame (used by tests/tools)."""
        frame = self.compositor.render(main_time, self.overlays, self.sync_points)
        self.last_frame = frame
        return frame

    def _do_render(self, _dt) -> None:
        self._render_pending = False
        frame = self.compositor.render(
            self.playback.current_time, self.overlays, self.sync_points
        )
        self.last_frame = frame
        if self.ui and frame is not None:
            self.ui.update_preview(frame, self.playback.current_time)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export(self) -> None:
        if not self.main_video or not self.overlays:
            self._status("请先导入主视频和嵌入视频")
            return
        pick_save_location(
            on_result=self._on_export_target,
            default_name="videoalign_export.mp4",
        )

    def _on_export_target(self, target) -> None:
        if not target:
            return
        self._status("开始导出（请稍候）…")
        overlay = self.overlays[0]

        def worker() -> None:
            tmp = os.path.join(cache_dir(), "tmp_export.mp4")
            try:
                from video.exporter import export_overlay_video

                export_overlay_video(self.main_video, overlay, self.sync_points, tmp)
                write_output(tmp, target)
                Clock.schedule_once(
                    lambda _dt: self._status("✅ 导出完成，已保存到所选位置")
                )
            except Exception as exc:
                Clock.schedule_once(lambda _dt: self._status(f"❌ 导出失败: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def on_pause(self) -> None:
        self.playback.pause()
        if self.ui:
            self.ui.on_playing_changed(False)

    def _status(self, message: str) -> None:
        if self.ui:
            Clock.schedule_once(lambda _dt: self.ui.set_status(message))
