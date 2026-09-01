"""Cross-platform file / save location picking.

- Android: uses the Storage Access Framework (SAF) through JNI intents, so no
  storage permission is required. Picked videos are copied into the app cache
  because OpenCV needs a real filesystem path.
- Desktop: falls back to Tkinter dialogs so the same code stays runnable on PC.
"""

from __future__ import annotations

import os
import shutil
import time

_IS_ANDROID = "ANDROID_ARGUMENT" in os.environ

_RESULT_OK = -1  # android.app.Activity.RESULT_OK


def is_android() -> bool:
    return _IS_ANDROID


def cache_dir() -> str:
    """Return a writable app-private directory."""
    base = (
        os.environ.get("ANDROID_CACHE_DIR")
        or os.environ.get("ANDROID_ARGUMENT")
        or os.path.join(os.path.expanduser("~"), ".videoalign")
    )
    os.makedirs(base, exist_ok=True)
    return base


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def pick_video(on_result) -> None:
    """Open a video picker and call ``on_result(path_or_None)``."""
    if _IS_ANDROID:
        _pick_android_file("video/*", on_result)
    else:
        _pick_desktop_video(on_result)


def pick_save_location(on_result, default_name: str) -> None:
    """Ask where to save and call ``on_result(target_or_None)``.

    On Android the target is a ``content://`` URI; on desktop it is a plain
    filesystem path. Pass it straight to :func:`write_output`.
    """
    if _IS_ANDROID:
        _pick_android_save(default_name, on_result)
    else:
        _pick_desktop_save(default_name, on_result)


def write_output(local_path: str, target) -> None:
    """Copy ``local_path`` into ``target`` (content:// URI or plain path)."""
    if _IS_ANDROID and not str(target).startswith("/"):
        _copy_to_uri(local_path, target)
    else:
        shutil.copyfile(local_path, str(target))


# ---------------------------------------------------------------------------
# Android (SAF via JNI)
# ---------------------------------------------------------------------------


def _android():
    from android import activity, mActivity
    from jnius import autoclass

    Intent = autoclass("android.content.Intent")
    return activity, mActivity, Intent


def _pick_android_file(mime: str, on_result) -> None:
    activity, mActivity, Intent = _android()
    request_code = 1001

    intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType(mime)

    def callback(request_code_, result_code, data):
        if request_code_ != request_code:
            return
        activity.unbind(on_activity_result=callback)
        try:
            if result_code != _RESULT_OK or not data:
                on_result(None)
                return
            uri = data.getData()
            path = _copy_uri_to_cache(uri)
            on_result(path)
        except Exception as exc:  # noqa: BLE001
            on_result(None)
            raise

    activity.bind(on_activity_result=callback)
    mActivity.startActivityForResult(intent, request_code)


def _pick_android_save(default_name: str, on_result) -> None:
    activity, mActivity, Intent = _android()
    request_code = 1002

    intent = Intent(Intent.ACTION_CREATE_DOCUMENT)
    intent.addCategory(Intent.CATEGORY_OPENABLE)
    intent.setType("video/mp4")
    intent.putExtra(Intent.EXTRA_TITLE, default_name)

    def callback(request_code_, result_code, data):
        if request_code_ != request_code:
            return
        activity.unbind(on_activity_result=callback)
        if result_code != _RESULT_OK or not data:
            on_result(None)
            return
        on_result(data.getData())

    activity.bind(on_activity_result=callback)
    mActivity.startActivityForResult(intent, request_code)


def _copy_uri_to_cache(uri) -> str:
    _, mActivity, _ = _android()
    resolver = mActivity.getContentResolver()
    stream = resolver.openInputStream(uri)
    name = _query_display_name(resolver, uri) or f"video_{int(time.time())}.mp4"
    dest = os.path.join(cache_dir(), os.path.basename(name))
    with open(dest, "wb") as out:
        shutil.copyfileobj(stream, out)
    return dest


def _copy_to_uri(local_path: str, uri) -> None:
    _, mActivity, _ = _android()
    resolver = mActivity.getContentResolver()
    out = resolver.openOutputStream(uri)
    try:
        with open(local_path, "rb") as src:
            shutil.copyfileobj(src, out)
    finally:
        out.close()


def _query_display_name(resolver, uri):
    try:
        cursor = resolver.query(uri, ["_display_name"], None, None, None)
        if cursor:
            try:
                if cursor.moveToFirst():
                    return cursor.getString(0)
            finally:
                cursor.close()
    except Exception:  # noqa: BLE001
        pass
    return None


# ---------------------------------------------------------------------------
# Desktop fallback (Tkinter)
# ---------------------------------------------------------------------------


def _pick_desktop_video(on_result) -> None:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    try:
        path = filedialog.askopenfilename(
            title="选择视频",
            filetypes=[
                ("视频文件", "*.mp4 *.mov *.mkv *.avi *.m4v *.webm"),
                ("所有文件", "*.*"),
            ],
        )
    finally:
        root.destroy()
    on_result(path or None)


def _pick_desktop_save(default_name: str, on_result) -> None:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    try:
        path = filedialog.asksaveasfilename(
            title="导出视频",
            defaultextension=".mp4",
            initialfile=default_name,
            filetypes=[("MP4 视频", "*.mp4"), ("所有文件", "*.*")],
        )
    finally:
        root.destroy()
    on_result(path or None)
