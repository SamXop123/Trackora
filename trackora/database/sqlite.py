"""SQLite-backed session storage."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from trackora.utils.time import duration_seconds, parse_timestamp, to_storage_timestamp


class SQLiteSessionStore:
    """Persist active and completed app sessions in SQLite."""

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
                    duration_seconds INTEGER
                )
                """
            )

    def start_session(self, *, app_name: str, window_title: str, start_time: str) -> int:
        """Insert a new active session and return its row id."""
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO app_sessions (
                    app_name,
                    window_title,
                    start_time,
                    end_time,
                    duration_seconds
                ) VALUES (?, ?, ?, NULL, NULL)
                """,
                (app_name, window_title, start_time),
            )
        return int(cursor.lastrowid)

    def end_session(self, *, session_id: int, end_time: str, duration: int) -> None:
        """Close an active session row."""
        with self._conn:
            self._conn.execute(
                """
                UPDATE app_sessions
                SET end_time = ?, duration_seconds = ?
                WHERE id = ?
                """,
                (end_time, duration, session_id),
            )

    def recover_open_sessions(self, closed_at: datetime) -> int:
        """
        Close leftover rows whose ``end_time`` is still NULL.

        This protects against a previous backend crash or power loss leaving
        stale active rows behind.
        """
        rows = self._conn.execute(
            """
            SELECT id, start_time
            FROM app_sessions
            WHERE end_time IS NULL
            """
        ).fetchall()

        if not rows:
            return 0

        end_time = to_storage_timestamp(closed_at)
        with self._conn:
            for row in rows:
                start_dt = parse_timestamp(str(row["start_time"])) or closed_at
                self._conn.execute(
                    """
                    UPDATE app_sessions
                    SET end_time = ?, duration_seconds = ?
                    WHERE id = ?
                    """,
                    (
                        end_time,
                        duration_seconds(start_dt, closed_at),
                        int(row["id"]),
                    ),
                )
        return len(rows)

    def close(self) -> None:
        """Close the SQLite connection."""
        self._conn.close()
