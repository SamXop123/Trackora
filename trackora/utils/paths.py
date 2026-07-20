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
    """Return the Trackora data directory under XDG data home (or Local AppData on Windows)."""
    import sys
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "trackora"
        return Path.home() / "AppData" / "Local" / "trackora"
    return xdg_data_home() / "trackora"


def default_state_path() -> Path:
    """Return the extension-written current window JSON path."""
    return trackora_data_dir() / "current_window.json"


def default_log_path() -> Path:
    """Return the log file path for background service diagnostic logs."""
    return trackora_data_dir() / "trackora.log"


def default_database_path() -> Path:
    """Return the SQLite database path."""
    return trackora_data_dir() / "trackora.db"


def default_lock_path() -> Path:
    """Return the singleton process lock path."""
    return trackora_data_dir() / "trackora.lock"


def get_asset_path(filename: str) -> Path:
    """Find the path to an asset, checking the package folder and standard system locations."""
    # 1. Package assets folder (when bundled inside the trackora package)
    package_assets = Path(__file__).resolve().parent.parent / "assets" / filename
    if package_assets.exists():
        return package_assets

    # 2. Sibling assets directory (fallback for older layouts/dev checkouts)
    git_assets = Path(__file__).resolve().parents[2] / "assets" / filename
    if git_assets.exists():
        return git_assets

    # 3. System shared assets path
    system_assets = Path("/usr/share/trackora/assets") / filename
    if system_assets.exists():
        return system_assets

    return package_assets

