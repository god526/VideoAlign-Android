"""FFmpeg subprocess runner with graceful fallback.

On Android the ffmpeg binary is bundled by python-for-android and lives inside
the app-private directory; on desktop we use a system ffmpeg or imageio-ffmpeg.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _candidate_paths() -> list[str]:
    """Return possible locations of the ffmpeg executable, most specific first."""
    candidates: list[str] = []

    env = os.environ.get("FFMPEG_BINARY")
    if env:
        candidates.append(env)

    which = shutil.which("ffmpeg")
    if which:
        candidates.append(which)

    # python-for-android: the ffmpeg recipe installs the binary into the
    # app-private directory (usually .../bin/ffmpeg).
    bases = [
        os.environ.get("ANDROID_ARGUMENT", ""),
        os.environ.get("ANDROID_PRIVATE", ""),
        os.environ.get("ANDROID_CACHE_DIR", ""),
        os.getcwd(),
        os.path.dirname(sys.executable) if sys.executable else "",
    ]
    for base in bases:
        if not base:
            continue
        candidates.append(os.path.join(base, "bin", "ffmpeg"))
        candidates.append(os.path.join(base, "ffmpeg"))

    # Desktop fallback: imageio-ffmpeg ships a bundled static ffmpeg.
    try:
        import imageio_ffmpeg

        candidates.append(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:  # noqa: BLE001
        pass

    return candidates


def find_ffmpeg() -> str | None:
    """Return the first usable FFmpeg executable."""
    for candidate in _candidate_paths():
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def run_ffmpeg(command: list[str], on_progress=None) -> subprocess.CompletedProcess:
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError(
            "未找到 FFmpeg。请安装 FFmpeg 并加入 PATH，"
            "或安装 Python 包 imageio-ffmpeg（桌面端），"
            "或确认 APK 已包含 ffmpeg recipe（Android 端）。"
        )

    if command and os.path.basename(command[0]).lower().startswith("ffmpeg"):
        command = [ffmpeg, *command[1:]]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert process.stdout is not None

    for line in process.stdout:
        if on_progress:
            on_progress(line)

    return process.wait()
