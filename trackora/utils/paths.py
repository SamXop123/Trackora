"""Filesystem path helpers for Trackora data files."""

from __future__ import annotations

import os
from pathlib import Path


def xdg_data_home() -> Path:
    """Return the user's XDG data directory."""
    base = os.environ.get("XDG_DATA_HOME")
    if base:
        return Path(base).expanduser()
    return Path.home() / ".local" / "share"


def trackora_data_dir() -> Path:
    """Return the Trackora data directory under XDG data home."""
    return xdg_data_home() / "trackora"


def default_state_path() -> Path:
    """Return the extension-written current window JSON path."""
    return trackora_data_dir() / "current_window.json"


def default_database_path() -> Path:
    """Return the SQLite database path."""
    return trackora_data_dir() / "trackora.db"


def default_lock_path() -> Path:
    """Return the singleton process lock path."""
    return trackora_data_dir() / "trackora.lock"
