"""Dataclasses used by the Trackora tracking backend."""

from trackora.models.dashboard import (
    ActiveAppStatus,
    AppUsageSummary,
    DashboardSnapshot,
    DailyUsageSummary,
    SessionRecord,
)
from trackora.models.session import ActiveSession
from trackora.models.window_state import WindowState

__all__ = [
    "ActiveAppStatus",
    "ActiveSession",
    "AppUsageSummary",
    "DashboardSnapshot",
    "DailyUsageSummary",
    "SessionRecord",
    "WindowState",
]
