"""Focused-window change detection, simple idle state-machine, and transitions."""

from __future__ import annotations

from datetime import datetime

from trackora.database import SQLiteSessionStore
from trackora.models.session import ActiveSession
from trackora.models.window_state import WindowState
from trackora.utils.logging import log_info, log_warning
from trackora.utils.time import duration_seconds, now_utc, parse_timestamp, to_storage_timestamp


class SessionTracker:
    """Turn sequential window snapshots into app session records using a simple state machine."""

    def __init__(self, store: SQLiteSessionStore, timeout_seconds: float = 10.0) -> None:
        self._store = store
        self._active_session: ActiveSession | None = None
        self.timeout_seconds = timeout_seconds
        self._is_idle: bool = True

    def process_window_state(self, state: WindowState) -> None:
        """Open or rotate sessions when the focused window changes."""
        now = now_utc()
        event_at = self._validated_event_time(state.timestamp)

        # Sleep/idle protection: if the window state timestamp is too old, treat it as idle/stale
        if duration_seconds(event_at, now) > self.timeout_seconds:
            self.process_idle_tick()
            return

        app_name = state.app.strip() or "Unknown"
        window_title = state.title.strip()

        if self._active_session is None:
            # Tracker was idle, now resumes
            log_info("tracker resumed")
            self._start_session(app_name, window_title, event_at)
            self._is_idle = False
        else:
            if self._matches_active(app_name, window_title):
                self._record_heartbeat(event_at)
            else:
                # App changed!
                log_info("active app changed")
                self._end_session(event_at)
                self._start_session(app_name, window_title, event_at)
                self._is_idle = False

    def process_idle_tick(self) -> None:
        """Handle periodic ticks when no valid or fresh window state is available."""
        now = now_utc()
        if self._active_session is not None:
            gap = duration_seconds(self._active_session.last_heartbeat_at, now)
            if gap > self.timeout_seconds:
                # Idle timeout exceeded
                self._end_session(self._active_session.last_heartbeat_at)
                log_info("tracker idle")
                self._is_idle = True

    def close_active_session(self) -> None:
        """Close the current active session gracefully without inflating post-heartbeat time."""
        if self._active_session is None:
            return

        closed_at = now_utc()
        active = self._active_session
        if closed_at < active.last_heartbeat_at:
            closed_at = active.last_heartbeat_at
        if duration_seconds(active.last_heartbeat_at, closed_at) > self.timeout_seconds:
            closed_at = active.last_heartbeat_at

        self._end_session(closed_at)

    def _matches_active(self, app_name: str, window_title: str) -> bool:
        active = self._active_session
        return (
            active is not None
            and active.app_name == app_name
            and active.window_title == window_title
        )

    def _start_session(self, app_name: str, window_title: str, event_at: datetime) -> None:
        event_time_text = to_storage_timestamp(event_at)
        session_id = self._store.start_session(
            app_name=app_name,
            window_title=window_title,
            start_time=event_time_text,
        )
        self._active_session = ActiveSession(
            session_id=session_id,
            app_name=app_name,
            window_title=window_title,
            start_at=event_at,
            start_time_text=event_time_text,
            last_heartbeat_at=event_at,
        )
        log_info("session started")
        log_info(f"Session started: {app_name}")
        log_info("Database updated")

    def _end_session(self, event_at: datetime) -> None:
        active = self._active_session
        if active is None:
            return

        event_time_text = to_storage_timestamp(event_at)
        duration = duration_seconds(active.start_at, event_at)
        self._store.end_session(
            session_id=active.session_id,
            end_time=event_time_text,
            duration=duration,
        )
        log_info("session ended")
        log_info(f"Session ended: {active.app_name} ({duration}s)")
        log_info("Database updated")
        self._active_session = None

    def _record_heartbeat(self, event_at: datetime) -> None:
        active = self._active_session
        if active is None:
            return
        event_time_text = to_storage_timestamp(event_at)
        self._store.record_heartbeat(
            session_id=active.session_id,
            heartbeat_time=event_time_text,
        )
        active.last_heartbeat_at = event_at

    def _validated_event_time(self, raw_timestamp: str) -> datetime:
        """
        Prefer extension timestamps, but never allow time to move backward.

        This protects duration math if the JSON timestamp is missing, stale,
        malformed, or older than the currently open session's start.
        """
        parsed = parse_timestamp(raw_timestamp) or now_utc()
        active = self._active_session
        if active is not None and parsed < active.last_heartbeat_at:
            log_warning(
                "Received out-of-order window timestamp; using current clock for safety"
            )
            return max(now_utc(), active.last_heartbeat_at)
        return parsed
