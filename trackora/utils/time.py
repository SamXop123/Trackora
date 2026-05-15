"""Timestamp parsing and duration helpers."""

from __future__ import annotations

from datetime import datetime, timezone


def now_utc() -> datetime:
    """Return the current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


def parse_timestamp(value: str) -> datetime | None:
    """Parse ISO-like timestamps from the extension or database."""
    text = value.strip()
    if not text:
        return None

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def to_storage_timestamp(value: datetime) -> str:
    """Format datetimes consistently for storage."""
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def duration_seconds(start: datetime, end: datetime) -> int:
    """Return a non-negative whole-second duration."""
    return max(int((end - start).total_seconds()), 0)
