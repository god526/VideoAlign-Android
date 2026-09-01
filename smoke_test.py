"""Automated smoke test: boots the Kivy app, imports two generated videos,
renders a composited frame, checks the preview texture, then exits.

Run: python smoke_test.py   (opens a window briefly and closes itself)
"""

from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("KIVY_NO_ARGS", "1")

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from kivy.app import App  # noqa: E402
from kivy.clock import Clock  # noqa: E402
from kivy.lang import Builder  # noqa: E402

from app_kivy.controller import VideoAlignController  # noqa: E402
from app_kivy.screen import MainScreen  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
Builder.load_file(os.path.join(_HERE, "main.kv"))

TMP = tempfile.mkdtemp(prefix="va_smoke_")


def make_video(path: str, w: int, h: int, fps: float, seconds: float, color: tuple) -> str:
    """Generate a tiny test video with a moving rectangle."""
    writer = cv2.VideoWriter(
        path, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h)
    )
    total = int(fps * seconds)
    for i in range(total):
        frame = np.full((h, w, 3), 40, dtype=np.uint8)
        x = int((w - 100) * i / max(total - 1, 1))
        cv2.rectangle(frame, (x, h // 4), (x + 100, h // 4 + 80), color, -1)
        writer.write(frame)
    writer.release()
    return path


def main() -> int:
    main_video = make_video(
        os.path.join(TMP, "main.mp4"), 640, 360, 24.0, 3.0, (200, 60, 60)
    )
    overlay_video = make_video(
        os.path.join(TMP, "overlay.mp4"), 320, 180, 24.0, 2.5, (60, 200, 60)
    )
    print(f"[smoke] main={main_video}")
    print(f"[smoke] overlay={overlay_video}")

    failures: list[str] = []

    class SmokeApp(App):
        title = "VideoAlign Smoke Test"

        def build(self):
            self.controller = VideoAlignController()
            return MainScreen(controller=self.controller)

        def on_start(self):
            Clock.schedule_once(self._run_steps, 0.5)

        def _run_steps(self, _dt):
            ctrl = self.controller
            try:
                # 1. import main video
                ctrl._on_main_picked(main_video)
                assert ctrl.main_video is not None, "main_video not set"
                print("[smoke] OK 导入主视频:", ctrl.main_video.display_name)

                # 2. import overlay
                ctrl._on_overlay_picked(overlay_video)
                assert len(ctrl.overlays) == 1, "overlay not added"
                print("[smoke] OK 添加嵌入视频:", ctrl.overlays[0].name)

                # 3. render a frame through the controller pipeline
                ctrl.seek(1.0)
                frame = ctrl.render_frame(ctrl.playback.current_time)
                assert frame is not None, "render returned None"
                print("[smoke] OK 合成帧:", frame.shape)

                # 4. push the frame into the preview widget (texture path)
                self.root.ids.preview.set_frame(frame)
                tex = self.root.ids.preview._texture
                assert tex is not None, "preview texture not created"
                print("[smoke] OK 预览纹理:", tex.size)

                # 5. drag simulation: move overlay to (10, 10)
                ov = ctrl.overlays[0]
                ov.transform.x, ov.transform.y = 10, 10
                ov.transform.clamp_to(ctrl.main_video.width, ctrl.main_video.height)
                assert (ov.transform.x, ov.transform.y) == (10, 10)
                print("[smoke] OK 拖动位置:", ov.transform.x, ov.transform.y)

                # 6. sync point + timeline labels
                ctrl.add_sync_point(1.0, 0.5)
                assert len(ctrl.sync_points) == 1
                print("[smoke] OK 同步点:", ctrl.sync_points[0])

                # 7. playback toggle
                ctrl.playback.set_duration(3.0)
                ctrl.playback.seek(0.0)
                print("[smoke] OK 时长:", round(ctrl.playback.duration, 2))

                print("[smoke] === 全部通过 ===")
            except Exception as exc:  # noqa: BLE001
                import traceback

                traceback.print_exc()
                failures.append(str(exc))
            finally:
                Clock.schedule_once(lambda _t: self.stop(), 0.3)

        def on_stop(self):
            ctrl = self.controller
            if ctrl:
                ctrl.compositor.close()

    SmokeApp().run()

    if failures:
        print("[smoke] FAILED:", failures)
        return 1
    print("[smoke] SUCCESS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
