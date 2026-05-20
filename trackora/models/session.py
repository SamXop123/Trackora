"""Session dataclasses for the tracker."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ActiveSession:
    """In-memory representation of the currently open app session."""

    session_id: int
    app_name: str
    window_title: str
    start_at: datetime
    start_time_text: str
    last_heartbeat_at: datetime
