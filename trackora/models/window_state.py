"""Structured focused-window state loaded from the extension JSON file."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowState:
    """Snapshot mirrored from ``current_window.json``."""

    app: str
    title: str
    timestamp: str
