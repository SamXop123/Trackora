"""Main background loop for reading window state and persisting sessions."""

from __future__ import annotations

import time
from pathlib import Path

from trackora.database import SQLiteSessionStore
from trackora.tracker import SessionTracker
from trackora.utils.lock import TrackoraAlreadyRunningError, TrackoraInstanceLock
from trackora.utils.logging import log_error, log_info, log_warning
from trackora.utils.paths import default_lock_path
from trackora.utils.time import now_utc
from trackora.window_state import read_window_state


def run_tracking_service(
    *,
    interval_sec: float,
    state_path: Path,
    database_path: Path,
    stop_flag: list[bool] | None = None,
    timeout_sec: float = 10.0,
) -> None:
    """Continuously convert focused-window snapshots into durable sessions."""
    if interval_sec <= 0:
        raise ValueError("interval_sec must be positive")

    lock = TrackoraInstanceLock(default_lock_path())
    if not lock.acquire():
        raise TrackoraAlreadyRunningError(
            "Trackora tracker is already running. No second tracker instance was started."
        )

    store = SQLiteSessionStore(database_path)
    store.initialize()

    recovered = store.recover_open_sessions(now_utc())
    if recovered:
        noun = "session" if recovered == 1 else "sessions"
        log_warning("Detected stale session gap from previous run")
        log_info(f"Recovered {recovered} stale {noun} safely")
        log_info("Database updated")

    tracker = SessionTracker(store, timeout_seconds=timeout_sec)
    last_error: str | None = None

    try:
        while stop_flag is None or not stop_flag[0]:
            result = read_window_state(state_path)
            
            try:
                if result.state is not None:
                    tracker.process_window_state(result.state)
                else:
                    tracker.process_idle_tick()
            except Exception as exc:
                log_error(f"Tracking error: {exc}")

            if result.state is None:
                if result.error != last_error:
                    log_warning(result.error or "No valid window state available")
                last_error = result.error
            else:
                if last_error is not None:
                    log_info("Window state input recovered")
                    last_error = None

            _sleep_in_slices(interval_sec, stop_flag)
    finally:
        try:
            try:
                tracker.close_active_session()
            finally:
                store.close()
        finally:
            lock.release()


def _sleep_in_slices(interval_sec: float, stop_flag: list[bool] | None) -> None:
    """Sleep in short increments so shutdown remains responsive."""
    remaining = float(interval_sec)
    step = min(0.2, remaining)
    while remaining > 0 and (stop_flag is None or not stop_flag[0]):
        time.sleep(step)
        remaining -= step
