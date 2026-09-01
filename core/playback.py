"""Timeline playback engine.

The engine is UI-toolkit agnostic. It advances a float ``current_time`` on a
timer and calls ``on_tick`` so the application can refresh its preview.
"""

from __future__ import annotations

import time
from typing import Callable


class PlaybackEngine:
    def __init__(
        self,
        after: Callable[[int, Callable[[], None]], None],
        interval_ms: int = 16,
    ):
        self._after = after
        self.interval_ms = interval_ms
        self.on_tick: Callable[[float], None] | None = None
        self.current_time = 0.0
        self.duration = 0.0
        self._playing = False
        self._last_timestamp: float | None = None
        self._after_id = None

    @property
    def playing(self) -> bool:
        return self._playing

    def set_duration(self, duration: float) -> None:
        self.duration = max(0.0, duration)
        self.current_time = min(self.current_time, self.duration)

    def play(self) -> None:
        if self._playing:
            return
        if self.duration <= 0:
            return
        if self.current_time >= self.duration:
            self.current_time = 0.0
        self._playing = True
        self._last_timestamp = time.perf_counter()
        self._schedule()

    def pause(self) -> None:
        self._playing = False
        self._last_timestamp = None
        if self._after_id is not None:
            self._after_id = None

    def toggle(self) -> None:
        if self._playing:
            self.pause()
        else:
            self.play()

    def seek(self, seconds: float) -> None:
        self.current_time = max(0.0, min(float(seconds), self.duration))
        self._last_timestamp = time.perf_counter() if self._playing else None
        self._emit()

    def step(self, delta: float) -> None:
        self.seek(self.current_time + delta)

    def stop(self) -> None:
        self.pause()
        self.current_time = 0.0
        self._emit()

    def _schedule(self) -> None:
        self._after_id = self._after(self.interval_ms, self._tick)

    def _tick(self) -> None:
        if not self._playing:
            return

        now = time.perf_counter()
        if self._last_timestamp is None:
            self._last_timestamp = now

        elapsed = now - self._last_timestamp
        self._last_timestamp = now
        self.current_time += elapsed

        if self.current_time >= self.duration:
            self.current_time = self.duration
            self.pause()

        self._emit()
        if self._playing:
            self._schedule()

    def _emit(self) -> None:
        if self.on_tick:
            self.on_tick(self.current_time)
