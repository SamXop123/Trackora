"""Focused-window change detection and session transitions."""

from __future__ import annotations

from trackora.database import SQLiteSessionStore
from trackora.models.session import ActiveSession
from trackora.models.window_state import WindowState
from trackora.utils.logging import log_info, log_warning
from trackora.utils.time import duration_seconds, now_utc, parse_timestamp, to_storage_timestamp


class SessionTracker:
    """Turn sequential window snapshots into app session records."""

    def __init__(self, store: SQLiteSessionStore) -> None:
        self._store = store
        self._active_session: ActiveSession | None = None

    def process_window_state(self, state: WindowState) -> None:
        """Open or rotate sessions when the focused window changes."""
        app_name = state.app.strip() or "Unknown"
        window_title = state.title.strip()
        event_at = self._validated_event_time(state.timestamp)
        event_time_text = to_storage_timestamp(event_at)

        if self._active_session is None:
            self._start_session(
                app_name=app_name,
                window_title=window_title,
                event_at=event_at,
                event_time_text=event_time_text,
            )
            return

        if self._matches_active(app_name, window_title):
            return

        self._end_session(event_at=event_at, event_time_text=event_time_text)
        self._start_session(
            app_name=app_name,
            window_title=window_title,
            event_at=event_at,
            event_time_text=event_time_text,
        )

    def close_active_session(self) -> None:
        """Close the current active session using the current clock time."""
        if self._active_session is None:
            return

        closed_at = now_utc()
        self._end_session(
            event_at=closed_at,
            event_time_text=to_storage_timestamp(closed_at),
        )

    def _matches_active(self, app_name: str, window_title: str) -> bool:
        active = self._active_session
        return (
            active is not None
            and active.app_name == app_name
            and active.window_title == window_title
        )

    def _start_session(
        self,
        *,
        app_name: str,
        window_title: str,
        event_at,
        event_time_text: str,
    ) -> None:
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
        )
        log_info(f"Session started: {app_name}")
        log_info("Database updated")

    def _end_session(self, *, event_at, event_time_text: str) -> None:
        active = self._active_session
        if active is None:
            return

        duration = duration_seconds(active.start_at, event_at)
        self._store.end_session(
            session_id=active.session_id,
            end_time=event_time_text,
            duration=duration,
        )
        log_info(f"Session ended: {active.app_name} ({duration}s)")
        log_info("Database updated")
        self._active_session = None

    def _validated_event_time(self, raw_timestamp: str):
        """
        Prefer extension timestamps, but never allow time to move backward.

        This protects duration math if the JSON timestamp is missing, stale,
        malformed, or older than the currently open session's start.
        """
        parsed = parse_timestamp(raw_timestamp) or now_utc()
        active = self._active_session
        if active is not None and parsed < active.start_at:
            log_warning(
                "Received out-of-order window timestamp; using current clock for safety"
            )
            return now_utc()
        return parsed
