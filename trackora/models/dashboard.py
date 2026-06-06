"""Dashboard-oriented data models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class SessionRecord:
    """Raw session row loaded from SQLite."""

    app_name: str
    window_title: str
    start_time: str
    end_time: str | None
    duration_seconds: int | None


@dataclass(frozen=True)
class AppUsageSummary:
    """Aggregated app usage for the current day."""

    app_name: str
    duration_seconds: int


@dataclass(frozen=True)
class AppDetailedStats:
    """Per-application statistics for the Applications page."""

    app_name: str
    duration_seconds: int
    session_count: int
    avg_session_seconds: int
    last_active: datetime | None


@dataclass(frozen=True)
class DailyUsageSummary:
    """One day's total usage."""

    day: date
    label: str
    duration_seconds: int


@dataclass(frozen=True)
class ActiveAppStatus:
    """Current active app inferred from the open session row."""

    app_name: str
    window_title: str
    started_at: datetime
    elapsed_seconds: int


@dataclass(frozen=True)
class TimelineSession:
    """A single session for the timeline view, with parsed datetimes."""

    app_name: str
    window_title: str
    start_time: datetime
    end_time: datetime
    duration_seconds: int


@dataclass(frozen=True)
class DashboardSnapshot:
    """All data needed to render one dashboard refresh."""

    total_today_seconds: int
    total_yesterday_seconds: int
    total_last7days_seconds: int
    total_today_sessions: int
    active_app: ActiveAppStatus | None
    top_apps: list[AppUsageSummary]
    all_apps: list[AppUsageSummary]
    hourly_labels: list[str]
    hourly_values: list[float]
    weekly_labels: list[str]
    weekly_values: list[float]
    weekly_days: list[DailyUsageSummary]
    last_refreshed: datetime
    status_message: str

    @classmethod
    def empty(cls, *, status_message: str) -> "DashboardSnapshot":
        return cls(
            total_today_seconds=0,
            total_yesterday_seconds=0,
            total_last7days_seconds=0,
            total_today_sessions=0,
            active_app=None,
            top_apps=[],
            all_apps=[],
            hourly_labels=[f"{hour:02d}" for hour in range(24)],
            hourly_values=[0.0] * 24,
            weekly_labels=[],
            weekly_values=[],
            weekly_days=[],
            last_refreshed=datetime.now().astimezone(),
            status_message=status_message,
        )


@dataclass(frozen=True)
class InsightsData:
    """Calculated productivity insights for the dashboard/insights view."""

    most_used_app_name: str
    most_used_app_duration: int
    most_used_app_percentage: int

    peak_hour_start: int
    peak_hour_duration: int

    longest_session_app: str
    longest_session_duration: int

    switches_today: int
    switches_yesterday: int | None

    usage_distribution: list[AppUsageSummary]
    hourly_activity: list[int]  # 24 buckets representing duration in seconds for each hour

    total_sessions_today: int
    avg_session_length_seconds: int
    most_active_app: str
    total_active_hours: float
    longest_focus_period_seconds: int

    category_breakdown: list[tuple[str, int, int]]  # category_name, duration_seconds, percentage


@dataclass(frozen=True)
class ReportsData:
    """Aggregated analytics for the Reports page over a date range."""

    total_screen_time_seconds: int
    total_sessions: int
    most_used_app_name: str
    most_used_app_duration: int
    most_active_day_label: str
    most_active_day_seconds: int

    daily_usage: list[DailyUsageSummary]
    app_usage: list[AppUsageSummary]
    category_breakdown: list[tuple[str, int, int]]  # category_name, duration_seconds, percentage

