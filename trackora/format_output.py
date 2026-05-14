"""Format stdout lines from ``WindowState`` (JSON written by the extension)."""

from __future__ import annotations
from datetime import datetime
from trackora.window_state import WindowState


def format_window_state_line(state: WindowState) -> str:
    """
    One human-readable line: ``[HH:MM:SS] App - Title``.

    Uses ``state.timestamp`` when it parses as ISO-like local time; otherwise
    falls back to the current clock.
    """
    ts_display = _format_timestamp_for_line(state.timestamp)
    app = state.app.strip() or "Unknown"
    title = state.title.strip() or ""
    return f"[{ts_display}] {app} - {title}"


def _format_timestamp_for_line(iso_or_empty: str) -> str:
    if not iso_or_empty:
        return datetime.now().strftime("%H:%M:%S")
    try:
        dt = datetime.fromisoformat(iso_or_empty)
        return dt.strftime("%H:%M:%S")
    except ValueError:
        return datetime.now().strftime("%H:%M:%S")
