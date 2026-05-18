"""Formatting helpers for Trackora CLI and GUI surfaces."""

from __future__ import annotations

from datetime import datetime


def format_duration_compact(total_seconds: int) -> str:
    """Format seconds into a compact human-readable duration."""
    total_seconds = max(int(total_seconds), 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def format_duration_live(total_seconds: int) -> str:
    """Format durations for a live activity timer."""
    total_seconds = max(int(total_seconds), 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {seconds:02d}s"
    return f"{seconds}s"


def format_duration_long(total_seconds: int) -> str:
    """Format seconds into a more descriptive duration."""
    total_seconds = max(int(total_seconds), 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours:
        return f"{hours} hr {minutes} min"
    return f"{minutes} min"


def format_last_refreshed(value: datetime) -> str:
    """Format a datetime for dashboard refresh labels."""
    return value.strftime("%H:%M:%S")


def format_duration_caption(total_seconds: int) -> str:
    """Format a duration for short explanatory labels."""
    total_seconds = max(int(total_seconds), 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours:
        return f"{hours} hr {minutes} min"
    return f"{minutes} min"
