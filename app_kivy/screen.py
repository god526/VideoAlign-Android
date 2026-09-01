"""Main screen: wires the Kivy widgets to the controller."""

from __future__ import annotations

from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout

from utils.timecode import format_tc


class MainScreen(BoxLayout):
    controller = ObjectProperty(None, allownone=True)

    def __init__(self, controller, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        controller.ui = self
        self._seeking = False  # suppress slider callbacks while we update it
        self.sync_a_time = 0.0
        self.sync_a_text = "00:00:00.000"

        # super().__init__ 已完成，kv 的 ids 已可用，安全初始化
        self.ids.preview.bind_controller(self.controller)
        self.controller._apply_state()
        self.set_status("请先导入主视频")

    # ------------------------------------------------------------------
    # UI events -> controller
    # ------------------------------------------------------------------

    def on_import_main(self):
        self.controller.import_main()

    def on_import_overlay(self):
        self.controller.import_overlay()

    def toggle_play(self):
        self.controller.toggle_play()

    def step_back(self):
        self.controller.step(-1.0)

    def step_forward(self):
        self.controller.step(1.0)

    def on_timeline_value(self, value: float):
        if self._seeking:
            return
        self.controller.seek(float(value))

    def set_sync_a(self):
        t = self.controller.playback.current_time
        self.sync_a_time = t
        self.sync_a_text = format_tc(t)
        self.ids.sync_a_label.text = f"A = {self.sync_a_text}"
        self.set_status(f"A 时间已设为当前播放位置 {self.sync_a_text}")

    def add_sync_point(self):
        try:
            b = float(self.ids.time_b.text.strip() or 0.0)
        except ValueError:
            b = 0.0
        self.controller.add_sync_point(self.sync_a_time, b)

    def undo_sync_point(self):
        self.controller.remove_last_sync_point()

    def on_export(self):
        self.controller.export()

    # ------------------------------------------------------------------
    # Controller callbacks -> UI
    # ------------------------------------------------------------------

    def on_project_changed(self, main_video, overlays, sync_points, duration):
        self.ids.timeline.max = max(duration, 0.001)
        self._seeking = True
        self.ids.timeline.value = 0.0
        self._seeking = False
        self.ids.time_label.text = f"{format_tc(0.0)} / {format_tc(duration)}"
        self.ids.sync_count.text = f"同步点: {len(sync_points)}"
        if main_video:
            self.ids.title_label.text = f"主视频: {main_video.display_name}"

    def on_playing_changed(self, playing: bool):
        self.ids.play_btn.text = "⏸" if playing else "▶"

    def on_sync_points_changed(self, sync_points):
        self.ids.sync_count.text = f"同步点: {len(sync_points)}"

    def update_preview(self, frame, current_time: float):
        self.ids.preview.set_frame(frame)
        self._seeking = True
        self.ids.timeline.max = max(self.controller.playback.duration, 0.001)
        self.ids.timeline.value = current_time
        self._seeking = False
        self.ids.time_label.text = (
            f"{format_tc(current_time)} / {format_tc(self.controller.playback.duration)}"
        )

    def set_status(self, message: str):
        self.ids.status_label.text = message
