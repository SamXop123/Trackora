"""SQLite-backed session storage."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from trackora.utils.time import duration_seconds, parse_timestamp, to_storage_timestamp


class SQLiteSessionStore:
    """Persist active and completed app sessions in SQLite."""

    _SESSION_COLUMNS = {
        "id",
        "app_name",
        "window_title",
        "start_time",
        "end_time",
        "duration_seconds",
        "last_heartbeat_time",
    }

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path.expanduser()
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._database_path)
        self._conn.row_factory = sqlite3.Row

    @property
    def database_path(self) -> Path:
        return self._database_path

    def initialize(self) -> None:
        """Create required tables if they do not already exist."""
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_name TEXT NOT NULL,
                    window_title TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
                    last_heartbeat_time TEXT
                )
                """
            )
            self._ensure_session_schema()
            self._conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_app_sessions_single_open
                ON app_sessions ((1))
                WHERE end_time IS NULL
                """
            )

    def start_session(self, *, app_name: str, window_title: str, start_time: str) -> int:
        """Insert a new active session and return its row id."""
        try:
            with self._conn:
                cursor = self._conn.execute(
                    """
                    INSERT INTO app_sessions (
                        app_name,
                        window_title,
                        start_time,
                        end_time,
                        duration_seconds,
                        last_heartbeat_time
                    ) VALUES (?, ?, ?, NULL, NULL, ?)
                    """,
                    (app_name, window_title, start_time, start_time),
                )
        except sqlite3.IntegrityError as exc:
            raise RuntimeError(
                "A tracker session is already active in the database"
            ) from exc
        return int(cursor.lastrowid)

    def record_heartbeat(self, *, session_id: int, heartbeat_time: str) -> None:
        """Persist the last successful tracking heartbeat for the active session."""
        with self._conn:
            self._conn.execute(
                """
                UPDATE app_sessions
                SET last_heartbeat_time = ?
                WHERE id = ?
                """,
                (heartbeat_time, session_id),
            )

    def end_session(self, *, session_id: int, end_time: str, duration: int) -> None:
        """Close an active session row."""
        with self._conn:
            self._conn.execute(
                """
                UPDATE app_sessions
                SET end_time = ?, duration_seconds = ?, last_heartbeat_time = ?
                WHERE id = ?
                """,
                (end_time, duration, end_time, session_id),
            )

    def recover_open_sessions(self, closed_at: datetime) -> int:
        """
        Close leftover rows whose ``end_time`` is still NULL.

        This protects against a previous backend crash or power loss leaving
        stale active rows behind.
        """
        rows = self._conn.execute(
            """
            SELECT id, app_name, start_time, last_heartbeat_time
            FROM app_sessions
            WHERE end_time IS NULL
            """
        ).fetchall()

        if not rows:
            return 0

        with self._conn:
            for row in rows:
                start_dt = parse_timestamp(str(row["start_time"])) or closed_at
                last_heartbeat_raw = str(row["last_heartbeat_time"] or "") or str(
                    row["start_time"]
                )
                recovered_end_dt = parse_timestamp(last_heartbeat_raw) or start_dt
                if recovered_end_dt < start_dt:
                    recovered_end_dt = start_dt
                end_time = to_storage_timestamp(recovered_end_dt)
                self._conn.execute(
                    """
                    UPDATE app_sessions
                    SET end_time = ?, duration_seconds = ?, last_heartbeat_time = ?
                    WHERE id = ?
                    """,
                    (
                        end_time,
                        duration_seconds(start_dt, recovered_end_dt),
                        end_time,
                        int(row["id"]),
                    ),
                )
        return len(rows)

    def active_session_exists(self) -> bool:
        """Return whether an open session row already exists."""
        row = self._conn.execute(
            """
            SELECT 1
            FROM app_sessions
            WHERE end_time IS NULL
            LIMIT 1
            """
        ).fetchone()
        return row is not None

    def close(self) -> None:
        """Close the SQLite connection."""
        self._conn.close()

    def _ensure_session_schema(self) -> None:
        """Perform lightweight schema migration for older local databases."""
        existing_columns = {
            str(row["name"])
            for row in self._conn.execute("PRAGMA table_info(app_sessions)").fetchall()
        }
        missing_columns = self._SESSION_COLUMNS - existing_columns
        if "last_heartbeat_time" in missing_columns:
            self._conn.execute(
                "ALTER TABLE app_sessions ADD COLUMN last_heartbeat_time TEXT"
            )
