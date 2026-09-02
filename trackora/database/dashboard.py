"""Read-only dashboard queries over the Trackora SQLite database.

Optimized with an O(N) epoch analytics engine, direct interval merging,
and zero-stat exclusions for instant sub-millisecond query performance.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from trackora.models.dashboard import (
    ActiveAppStatus,
    AppDetailedStats,
    AppUsageSummary,
    DashboardSnapshot,
    DailyUsageSummary,
    SessionRecord,
    TimelineSession,
    InsightsData,
    ReportsData,
)
from trackora.utils.app_names import normalize_app_name
from trackora.utils.time import duration_seconds, now_utc, parse_timestamp
from trackora.utils.grouping import merge_consecutive_sessions
from trackora.utils.settings import settings_manager


def _get_app_category(name: str) -> str:
    name_lower = name.lower()
    
    # 1. Browsers
    if any(kw in name_lower for kw in ["chrome", "brave", "firefox", "edge", "chromium", "safari", "opera", "vivaldi", "browser"]):
        return "Browsers"
        
    # 2. Development
    if any(kw in name_lower for kw in ["vs code", "vscode", "cursor", "github desktop", "terminal", "antigravity", "kitty", "console", "sublime", "pycharm", "webstorm", "intellij", "git", "github", "neovim", "vim", "emacs", "bash", "sh", "trackora"]):
        return "Development"
        
    # 3. Music
    if any(kw in name_lower for kw in ["spotify", "music", "rhythmbox", "vlc", "audacious", "clementine", "itunes", "deezer"]):
        return "Music"
        
    # 4. Communication
    if any(kw in name_lower for kw in ["discord", "slack", "telegram", "whatsapp", "teams", "zoom", "skype", "signal", "messenger", "wechat", "mail", "outlook", "thunderbird"]):
        return "Communication"
        
    # 5. System
    if any(kw in name_lower for kw in ["gnome software", "gnome-software", "settings", "system settings", "gnome-control-center", "task manager", "monitor", "finder", "explorer", "dbus", "xorg", "system tools"]):
        return "System"
        
    # 6. Utilities
    if any(kw in name_lower for kw in ["files", "nautilus", "archive manager", "archive", "file roller", "text editor", "gedit", "kwrite", "calculator", "notes", "obsidian", "notion", "keep", "manager", "document viewer", "papers"]):
        return "Utilities"
        
    return "Other"


def _merge_float_intervals(intervals: list[tuple[float, float]]) -> int:
    """Fast linear float interval merging in seconds."""
    if not intervals:
        return 0
    intervals.sort(key=lambda x: x[0])
    total = 0.0
    cur_start, cur_end = intervals[0]
    for s, e in intervals[1:]:
        if s <= cur_end:
            if e > cur_end:
                cur_end = e
        else:
            total += cur_end - cur_start
            cur_start, cur_end = s, e
    total += cur_end - cur_start
    return int(total)


def _parse_row_epoch(row: sqlite3.Row, now_epoch: float) -> tuple[str, str, float, float] | None:
    """Extract and parse SQLite session row into (normalized_app, window_title, start_epoch, end_epoch)."""
    st_str = row["start_time"]
    if not st_str:
        return None
    if st_str.endswith("Z"):
        st_str = st_str[:-1] + "+00:00"
    try:
        s_epoch = datetime.fromisoformat(st_str).timestamp()
    except (ValueError, TypeError):
        return None

    et_str = row["end_time"]
    if et_str:
        if et_str.endswith("Z"):
            et_str = et_str[:-1] + "+00:00"
        try:
            e_epoch = datetime.fromisoformat(et_str).timestamp()
        except (ValueError, TypeError):
            e_epoch = now_epoch
    else:
        e_epoch = now_epoch

    if e_epoch <= s_epoch:
        return None

    app_raw = str(row["app_name"] or "")
    win_title = str(row["window_title"] or "")
    if settings_manager.is_application_excluded(app_raw, win_title):
        return None

    app_name = normalize_app_name(app_raw, win_title)
    return (app_name, win_title, s_epoch, e_epoch)


class DashboardRepository:
    """Load dashboard-friendly summaries from the Trackora database."""

    _MIN_MEANINGFUL_APP_SECONDS = 1

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path.expanduser()
        self._query_cache: dict[str, tuple[float, float, Any]] = {}
        self._ensure_indexes()

    def _get_query_cache(self, key: str, ttl: float = 3.0) -> Any | None:
        if not self._database_path.exists():
            return None
        cached = self._query_cache.get(key)
        if not cached:
            return None
        cached_time, cached_mtime, data = cached
        now = datetime.now(timezone.utc).timestamp()
        if (now - cached_time) > ttl:
            return None
        try:
            mtime = self._database_path.stat().st_mtime
            if mtime != cached_mtime:
                return None
        except Exception:
            return None
        return data

    def _set_query_cache(self, key: str, data: Any) -> None:
        try:
            mtime = self._database_path.stat().st_mtime
            now = datetime.now(timezone.utc).timestamp()
            self._query_cache[key] = (now, mtime, data)
        except Exception:
            pass

    def _ensure_indexes(self) -> None:
        if not self._database_path.exists():
            return
        try:
            with sqlite3.connect(self._database_path, timeout=1.0) as conn:
                conn.execute("CREATE INDEX IF NOT EXISTS idx_app_sessions_times ON app_sessions (start_time, end_time)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_app_sessions_open ON app_sessions (end_time) WHERE end_time IS NULL")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_app_sessions_app_name ON app_sessions (app_name)")
        except Exception:
            pass

    def load_snapshot(self, target_date: date | None = None) -> DashboardSnapshot:
        """Build a full dashboard snapshot from persisted session rows."""
        if not self._database_path.exists():
            return DashboardSnapshot.empty(
                status_message=f"Database not found: {self._database_path}"
            )

        now = now_utc()
        now_epoch = now.timestamp()
        local_now = now.astimezone()
        today_local = target_date if target_date is not None else local_now.date()
        yesterday_local = today_local - timedelta(days=1)
        week_start_local = today_local - timedelta(days=6)
        
        day_start_utc, day_end_utc = self._local_day_bounds(today_local, local_now)
        yesterday_start_utc, yesterday_end_utc = self._local_day_bounds(
            yesterday_local,
            local_now,
        )
        week_start_utc, _ = self._local_day_bounds(week_start_local, local_now)

        day_start_epoch = day_start_utc.timestamp()
        day_end_epoch = day_end_utc.timestamp()
        yesterday_start_epoch = yesterday_start_utc.timestamp()
        yesterday_end_epoch = yesterday_end_utc.timestamp()

        try:
            with sqlite3.connect(self._database_path, timeout=2.0) as conn:
                conn.row_factory = sqlite3.Row
                session_rows = conn.execute(
                    """
                    SELECT app_name, window_title, start_time, end_time, duration_seconds
                    FROM app_sessions
                    WHERE start_time < ?
                      AND COALESCE(end_time, ?) > ?
                    ORDER BY start_time ASC
                    """,
                    (
                        self._to_sql_timestamp(day_end_utc),
                        self._to_sql_timestamp(now),
                        self._to_sql_timestamp(week_start_utc),
                    ),
                ).fetchall()
                active_row = conn.execute(
                    """
                    SELECT app_name, window_title, start_time, last_heartbeat_time
                    FROM app_sessions
                    WHERE end_time IS NULL
                    ORDER BY start_time DESC
                    LIMIT 1
                    """
                ).fetchone()
        except sqlite3.Error as exc:
            return DashboardSnapshot.empty(
                status_message=f"Could not read database: {exc}"
            )

        # Pre-parse session rows into epochs
        parsed_today: list[tuple[str, str, float, float]] = []
        parsed_yesterday: list[tuple[str, str, float, float]] = []
        parsed_all_week: list[tuple[str, str, float, float]] = []

        for row in session_rows:
            parsed = _parse_row_epoch(row, now_epoch)
            if not parsed:
                continue
            parsed_all_week.append(parsed)
            _, _, s_epoch, e_epoch = parsed
            if e_epoch > day_start_epoch and s_epoch < day_end_epoch:
                parsed_today.append(parsed)
            if e_epoch > yesterday_start_epoch and s_epoch < yesterday_end_epoch:
                parsed_yesterday.append(parsed)

        # Today's clipped intervals by app
        today_intervals_by_app: dict[str, list[tuple[float, float]]] = {}
        today_intervals_flat: list[tuple[float, float]] = []
        for app_name, _, s_epoch, e_epoch in parsed_today:
            cs = max(s_epoch, day_start_epoch)
            ce = min(e_epoch, day_end_epoch)
            if ce > cs:
                today_intervals_by_app.setdefault(app_name, []).append((cs, ce))
                today_intervals_flat.append((cs, ce))

        # Yesterday's flat intervals
        yesterday_intervals_flat: list[tuple[float, float]] = []
        for _, _, s_epoch, e_epoch in parsed_yesterday:
            cs = max(s_epoch, yesterday_start_epoch)
            ce = min(e_epoch, yesterday_end_epoch)
            if ce > cs:
                yesterday_intervals_flat.append((cs, ce))

        # Weekly days aggregation (7 days)
        tz = local_now.tzinfo
        weekly_bounds = []
        for offset in range(7):
            d = week_start_local + timedelta(days=offset)
            s_dt = datetime.combine(d, time.min, tzinfo=tz)
            e_dt = s_dt + timedelta(days=1)
            weekly_bounds.append((s_dt.timestamp(), e_dt.timestamp(), d, d.strftime("%a\n%d")))

        weekly_day_intervals = [[] for _ in range(7)]
        for _, _, s_epoch, e_epoch in parsed_all_week:
            for i, (ds, de, _, _) in enumerate(weekly_bounds):
                if e_epoch > ds and s_epoch < de:
                    weekly_day_intervals[i].append((max(s_epoch, ds), min(e_epoch, de)))

        weekly_days = [
            DailyUsageSummary(
                day=d,
                label=lbl,
                duration_seconds=_merge_float_intervals(weekly_day_intervals[i]),
            )
            for i, (_, _, d, lbl) in enumerate(weekly_bounds)
        ]

        # App usage list for today
        usage_by_app = {
            app_name: _merge_float_intervals(intervals)
            for app_name, intervals in today_intervals_by_app.items()
        }
        sorted_usage = sorted(
            usage_by_app.items(),
            key=lambda item: (-item[1], item[0].lower()),
        )
        top_apps = [
            AppUsageSummary(app_name=app_name, duration_seconds=seconds)
            for app_name, seconds in sorted_usage
        ]
        meaningful_apps = [
            item for item in top_apps
            if item.duration_seconds >= self._MIN_MEANINGFUL_APP_SECONDS
        ]

        # Hourly activity (24 buckets)
        hourly_seconds = [0] * 24
        for hour in range(24):
            b_start_dt = datetime.combine(today_local, time(hour=hour), tzinfo=tz)
            b_end_dt = b_start_dt + timedelta(hours=1)
            bs_epoch = b_start_dt.timestamp()
            be_epoch = b_end_dt.timestamp()
            h_intervals = []
            for _, _, s_epoch, e_epoch in parsed_today:
                if e_epoch > bs_epoch and s_epoch < be_epoch:
                    h_intervals.append((max(s_epoch, bs_epoch), min(e_epoch, be_epoch)))
            hourly_seconds[hour] = _merge_float_intervals(h_intervals)

        active_app = self._active_app_status(active_row, now)
        total_seconds = _merge_float_intervals(today_intervals_flat)
        total_yesterday_seconds = _merge_float_intervals(yesterday_intervals_flat)
        total_last7days_seconds = sum(day.duration_seconds for day in weekly_days)
        view_time = datetime.combine(today_local, local_now.time(), tzinfo=local_now.tzinfo)

        return DashboardSnapshot(
            total_today_seconds=total_seconds,
            total_yesterday_seconds=total_yesterday_seconds,
            total_last7days_seconds=total_last7days_seconds,
            total_today_sessions=len(parsed_today),
            active_app=active_app,
            top_apps=meaningful_apps[:5],
            all_apps=meaningful_apps,
            hourly_labels=[f"{hour:02d}" for hour in range(24)],
            hourly_values=[round(seconds / 3600, 2) for seconds in hourly_seconds],
            weekly_labels=[day.label for day in weekly_days],
            weekly_values=[round(day.duration_seconds / 3600, 2) for day in weekly_days],
            weekly_days=weekly_days,
            last_refreshed=view_time,
            status_message="Connected to Trackora database",
        )

    def load_active_app(self) -> ActiveAppStatus | None:
        """Fetch the current active app status, checking for staleness."""
        if not self._database_path.exists():
            return None

        now = now_utc()
        try:
            with sqlite3.connect(self._database_path, timeout=1.0) as conn:
                conn.row_factory = sqlite3.Row
                active_row = conn.execute(
                    """
                    SELECT app_name, window_title, start_time, last_heartbeat_time
                    FROM app_sessions
                    WHERE end_time IS NULL
                    ORDER BY start_time DESC
                    LIMIT 1
                    """
                ).fetchone()
        except sqlite3.Error:
            return None

        return self._active_app_status(active_row, now)

    def load_timeline_sessions(self) -> list[TimelineSession]:
        """Load today's sessions for the timeline page, newest first."""
        if not self._database_path.exists():
            return []

        now = now_utc()
        now_epoch = now.timestamp()
        local_now = now.astimezone()
        today_local = local_now.date()
        day_start_utc, day_end_utc = self._local_day_bounds(today_local, local_now)
        day_start_epoch = day_start_utc.timestamp()
        day_end_epoch = day_end_utc.timestamp()

        try:
            with sqlite3.connect(self._database_path, timeout=2.0) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT app_name, window_title, start_time, end_time, duration_seconds
                    FROM app_sessions
                    WHERE start_time < ?
                      AND COALESCE(end_time, ?) > ?
                    ORDER BY start_time DESC
                    """,
                    (
                        self._to_sql_timestamp(day_end_utc),
                        self._to_sql_timestamp(now),
                        self._to_sql_timestamp(day_start_utc),
                    ),
                ).fetchall()
        except sqlite3.Error:
            return []

        sessions: list[TimelineSession] = []
        tz = timezone.utc
        for row in rows:
            parsed = _parse_row_epoch(row, now_epoch)
            if not parsed:
                continue
            app_name, win_title, s_epoch, e_epoch = parsed
            if e_epoch <= day_start_epoch or s_epoch >= day_end_epoch:
                continue
            cs_epoch = max(s_epoch, day_start_epoch)
            ce_epoch = min(e_epoch, day_end_epoch)
            dur = int(ce_epoch - cs_epoch)
            if dur <= 0:
                continue

            sessions.append(TimelineSession(
                app_name=app_name,
                window_title=win_title,
                start_time=datetime.fromtimestamp(cs_epoch, tz),
                end_time=datetime.fromtimestamp(ce_epoch, tz),
                duration_seconds=dur,
            ))
        return sessions

    def load_app_details(self, *, days: int = 1) -> list[AppDetailedStats]:
        """Per-app stats for the Applications page over a given day range."""
        if not self._database_path.exists():
            return []

        cache_key = f"app_details_{days}"
        cached = self._get_query_cache(cache_key)
        if cached is not None:
            return cached

        now = now_utc()
        now_epoch = now.timestamp()
        local_now = now.astimezone()
        today_local = local_now.date()
        range_start_local = today_local - timedelta(days=max(days - 1, 0))
        range_start_utc, _ = self._local_day_bounds(range_start_local, local_now)
        _, range_end_utc = self._local_day_bounds(today_local, local_now)
        range_start_epoch = range_start_utc.timestamp()
        range_end_epoch = range_end_utc.timestamp()

        try:
            with sqlite3.connect(self._database_path, timeout=2.0) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT app_name, window_title, start_time, end_time, duration_seconds
                    FROM app_sessions
                    WHERE start_time < ?
                      AND COALESCE(end_time, ?) > ?
                    ORDER BY start_time ASC
                    """,
                    (
                        self._to_sql_timestamp(range_end_utc),
                        self._to_sql_timestamp(now),
                        self._to_sql_timestamp(range_start_utc),
                    ),
                ).fetchall()
        except sqlite3.Error:
            return []

        app_intervals: dict[str, list[tuple[float, float]]] = {}
        app_session_counts: dict[str, int] = {}
        app_last_active_epoch: dict[str, float] = {}

        for row in rows:
            parsed = _parse_row_epoch(row, now_epoch)
            if not parsed:
                continue
            app_name, _, s_epoch, e_epoch = parsed
            if e_epoch <= range_start_epoch or s_epoch >= range_end_epoch:
                continue
            cs = max(s_epoch, range_start_epoch)
            ce = min(e_epoch, range_end_epoch)
            if ce <= cs:
                continue
            app_intervals.setdefault(app_name, []).append((cs, ce))
            app_session_counts[app_name] = app_session_counts.get(app_name, 0) + 1
            prev = app_last_active_epoch.get(app_name)
            if prev is None or ce > prev:
                app_last_active_epoch[app_name] = ce

        results: list[AppDetailedStats] = []
        tz = local_now.tzinfo
        for app_name, intervals in app_intervals.items():
            total = _merge_float_intervals(intervals)
            if total < self._MIN_MEANINGFUL_APP_SECONDS:
                continue
            count = app_session_counts[app_name]
            last_act = datetime.fromtimestamp(app_last_active_epoch[app_name], timezone.utc).astimezone(tz) if app_name in app_last_active_epoch else None
            results.append(AppDetailedStats(
                app_name=app_name,
                duration_seconds=total,
                session_count=count,
                avg_session_seconds=total // max(count, 1),
                last_active=last_act,
            ))
        results.sort(key=lambda x: (-x.duration_seconds, x.app_name.lower()))
        self._set_query_cache(cache_key, results)
        return results

    def _to_session_record(self, row: sqlite3.Row) -> SessionRecord:
        return SessionRecord(
            app_name=normalize_app_name(
                str(row["app_name"] or "Unknown"),
                str(row["window_title"] or ""),
            ),
            window_title=str(row["window_title"] or ""),
            start_time=str(row["start_time"] or ""),
            end_time=str(row["end_time"] or "") or None,
            duration_seconds=int(row["duration_seconds"]) if row["duration_seconds"] is not None else None,
        )

    def _intersects_day(
        self,
        session: SessionRecord,
        day_start_utc: datetime,
        day_end_utc: datetime,
        now: datetime,
    ) -> bool:
        start = parse_timestamp(session.start_time)
        if start is None:
            return False
        parsed_end = parse_timestamp(session.end_time) if session.end_time else now
        if parsed_end is None:
            return False
        return parsed_end > day_start_utc and start < day_end_utc

    def _aggregate_app_usage(
        self,
        *,
        normalized_sessions: list[tuple[str, datetime, datetime]],
        day_start_utc: datetime,
        day_end_utc: datetime,
    ) -> list[AppUsageSummary]:
        intervals_by_app: dict[str, list[tuple[datetime, datetime]]] = {}
        for app_name, start, end in normalized_sessions:
            clipped_start = max(start, day_start_utc)
            clipped_end = min(end, day_end_utc)
            if clipped_end <= clipped_start:
                continue
            intervals_by_app.setdefault(app_name, []).append((clipped_start, clipped_end))

        usage_by_app = {
            app_name: self._merged_intervals_seconds(intervals)
            for app_name, intervals in intervals_by_app.items()
        }

        sorted_usage = sorted(
            usage_by_app.items(),
            key=lambda item: (-item[1], item[0].lower()),
        )
        return [
            AppUsageSummary(app_name=app_name, duration_seconds=seconds)
            for app_name, seconds in sorted_usage
        ]

    def _filter_meaningful_app_usage(
        self,
        app_usage: list[AppUsageSummary],
    ) -> list[AppUsageSummary]:
        meaningful = [
            item
            for item in app_usage
            if item.duration_seconds >= self._MIN_MEANINGFUL_APP_SECONDS
        ]
        return meaningful

    def _build_hourly_buckets(
        self,
        *,
        normalized_sessions: list[tuple[str, datetime, datetime]],
        today_local: date,
        tzinfo,
        now: datetime,
    ) -> list[int]:
        buckets = [0] * 24
        for hour in range(24):
            bucket_start_local = datetime.combine(today_local, time(hour=hour), tzinfo=tzinfo)
            bucket_end_local = bucket_start_local + timedelta(hours=1)
            bucket_start_utc = bucket_start_local.astimezone(now.tzinfo)
            bucket_end_utc = bucket_end_local.astimezone(now.tzinfo)
            intervals = []
            for _app_name, start, end in normalized_sessions:
                overlap_start = max(start, bucket_start_utc)
                overlap_end = min(end, bucket_end_utc)
                if overlap_end > overlap_start:
                    intervals.append((overlap_start, overlap_end))
            buckets[hour] = self._merged_intervals_seconds(intervals)
        return buckets

    def _active_app_status(
        self,
        active_row: sqlite3.Row | None,
        now: datetime,
    ) -> ActiveAppStatus | None:
        if active_row is None:
            return None

        start_time_text = str(active_row["start_time"] or "")
        started_at = parse_timestamp(start_time_text)
        if started_at is None:
            return None

        last_hb_text = ""
        try:
            if "last_heartbeat_time" in active_row.keys():
                last_hb_text = str(active_row["last_heartbeat_time"] or "")
        except Exception:
            pass

        last_hb = parse_timestamp(last_hb_text) if last_hb_text else started_at
        if last_hb is not None:
            if duration_seconds(last_hb, now) > 20:
                return None

        raw_app = str(active_row["app_name"] or "Unknown")
        raw_title = str(active_row["window_title"] or "")
        if settings_manager.is_application_excluded(raw_app, raw_title):
            return None

        return ActiveAppStatus(
            app_name=normalize_app_name(raw_app, raw_title),
            window_title=raw_title,
            started_at=started_at,
            elapsed_seconds=duration_seconds(started_at, now),
        )

    def _build_weekly_daily_totals(
        self,
        *,
        sessions: list[SessionRecord],
        start_day: date,
        local_now: datetime,
        now: datetime,
    ) -> list[DailyUsageSummary]:
        days: list[DailyUsageSummary] = []
        for offset in range(7):
            day = start_day + timedelta(days=offset)
            day_start_utc, day_end_utc = self._local_day_bounds(day, local_now)
            day_sessions = [
                session
                for session in sessions
                if self._intersects_day(session, day_start_utc, day_end_utc, now)
            ]
            normalized = self._normalized_sessions(
                todays_sessions=day_sessions,
                day_start_utc=day_start_utc,
                day_end_utc=day_end_utc,
                now=now,
            )
            days.append(
                DailyUsageSummary(
                    day=day,
                    label=day.strftime("%a\n%d"),
                    duration_seconds=self._merged_total_seconds(normalized),
                )
            )
        return days

    def _normalized_sessions(
        self,
        *,
        todays_sessions: list[SessionRecord],
        day_start_utc: datetime,
        day_end_utc: datetime,
        now: datetime,
    ) -> list[tuple[str, datetime, datetime]]:
        normalized: list[tuple[str, datetime, datetime]] = []
        for session in todays_sessions:
            start = parse_timestamp(session.start_time)
            if start is None:
                continue
            parsed_end = parse_timestamp(session.end_time) if session.end_time else now
            if parsed_end is None:
                continue
            end = parsed_end
            if end <= start:
                continue
            clipped_start = max(start, day_start_utc)
            clipped_end = min(end, day_end_utc)
            if clipped_end <= clipped_start:
                continue
            app_name = session.app_name.strip() or "Unknown"
            normalized.append((app_name, clipped_start, clipped_end))
        return normalized

    def _merged_total_seconds(
        self,
        normalized_sessions: list[tuple[str, datetime, datetime]],
    ) -> int:
        intervals = [(start, end) for _app_name, start, end in normalized_sessions]
        return self._merged_intervals_seconds(intervals)

    def _merged_intervals_seconds(
        self,
        intervals: list[tuple[datetime, datetime]],
    ) -> int:
        if not intervals:
            return 0

        sorted_intervals = sorted(intervals, key=lambda item: item[0])
        total = 0
        current_start, current_end = sorted_intervals[0]

        for start, end in sorted_intervals[1:]:
            if start <= current_end:
                if end > current_end:
                    current_end = end
                continue
            total += duration_seconds(current_start, current_end)
            current_start, current_end = start, end

        total += duration_seconds(current_start, current_end)
        return total

    def _local_day_bounds(
        self,
        local_day: date,
        local_now: datetime,
    ) -> tuple[datetime, datetime]:
        day_start_local = datetime.combine(local_day, time.min, tzinfo=local_now.tzinfo)
        day_end_local = day_start_local + timedelta(days=1)
        return (
            day_start_local.astimezone(now_utc().tzinfo),
            day_end_local.astimezone(now_utc().tzinfo),
        )

    def _to_sql_timestamp(self, value: datetime) -> str:
        return value.astimezone(now_utc().tzinfo).isoformat().replace("+00:00", "Z")

    def load_insights_data(self) -> InsightsData | None:
        """Calculate and return insights data for today and yesterday."""
        if not self._database_path.exists():
            return None

        now = now_utc()
        now_epoch = now.timestamp()
        local_now = now.astimezone()
        today_local = local_now.date()
        yesterday_local = today_local - timedelta(days=1)

        day_start_utc, day_end_utc = self._local_day_bounds(today_local, local_now)
        yesterday_start_utc, yesterday_end_utc = self._local_day_bounds(yesterday_local, local_now)
        day_start_epoch = day_start_utc.timestamp()
        day_end_epoch = day_end_utc.timestamp()
        yesterday_start_epoch = yesterday_start_utc.timestamp()
        yesterday_end_epoch = yesterday_end_utc.timestamp()

        try:
            with sqlite3.connect(self._database_path, timeout=2.0) as conn:
                conn.row_factory = sqlite3.Row
                today_rows = conn.execute(
                    """
                    SELECT app_name, window_title, start_time, end_time, duration_seconds
                    FROM app_sessions
                    WHERE start_time < ?
                      AND COALESCE(end_time, ?) > ?
                    ORDER BY start_time ASC
                    """,
                    (
                        self._to_sql_timestamp(day_end_utc),
                        self._to_sql_timestamp(now),
                        self._to_sql_timestamp(day_start_utc),
                    ),
                ).fetchall()

                yesterday_rows = conn.execute(
                    """
                    SELECT app_name, window_title, start_time, end_time, duration_seconds
                    FROM app_sessions
                    WHERE start_time < ?
                      AND COALESCE(end_time, ?) > ?
                    ORDER BY start_time ASC
                    """,
                    (
                        self._to_sql_timestamp(yesterday_end_utc),
                        self._to_sql_timestamp(now),
                        self._to_sql_timestamp(yesterday_start_utc),
                    ),
                ).fetchall()
        except sqlite3.Error:
            return None

        tz = timezone.utc
        sessions: list[TimelineSession] = []
        for row in today_rows:
            parsed = _parse_row_epoch(row, now_epoch)
            if not parsed:
                continue
            app_name, win_title, s_epoch, e_epoch = parsed
            if e_epoch <= day_start_epoch or s_epoch >= day_end_epoch:
                continue
            cs_epoch = max(s_epoch, day_start_epoch)
            ce_epoch = min(e_epoch, day_end_epoch)
            dur = int(ce_epoch - cs_epoch)
            if dur <= 0:
                continue
            sessions.append(TimelineSession(
                app_name=app_name,
                window_title=win_title,
                start_time=datetime.fromtimestamp(cs_epoch, tz),
                end_time=datetime.fromtimestamp(ce_epoch, tz),
                duration_seconds=dur,
            ))

        if not sessions:
            return None

        grouped_sessions = merge_consecutive_sessions(sessions)
        if not grouped_sessions:
            return None

        total_sessions_today = len(grouped_sessions)
        avg_session_length_seconds = int(sum(s.duration_seconds for s in grouped_sessions) / len(grouped_sessions))

        app_durations: dict[str, int] = {}
        for s in grouped_sessions:
            app_durations[s.app_name] = app_durations.get(s.app_name, 0) + s.duration_seconds

        total_duration_today = sum(app_durations.values())
        most_used_app_name = max(app_durations, key=lambda k: app_durations[k]) if app_durations else ""
        most_used_app_duration = app_durations[most_used_app_name] if most_used_app_name else 0
        most_used_app_percentage = int((most_used_app_duration / total_duration_today) * 100) if total_duration_today > 0 else 0

        # Hourly activity
        hourly_activity = [0] * 24
        for s in sessions:
            local_start = s.start_time.astimezone()
            local_end = s.end_time.astimezone()
            curr = local_start
            while curr < local_end:
                next_hour = (curr + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                chunk_end = min(local_end, next_hour)
                bucket_idx = curr.hour
                hourly_activity[bucket_idx] += int((chunk_end - curr).total_seconds())
                curr = chunk_end

        peak_hour_start = hourly_activity.index(max(hourly_activity)) if any(hourly_activity) else 0
        peak_hour_duration = hourly_activity[peak_hour_start]

        longest_s = max(grouped_sessions, key=lambda s: s.duration_seconds)
        longest_session_app = longest_s.app_name
        longest_session_duration = longest_s.duration_seconds

        yesterday_sessions: list[TimelineSession] = []
        for row in yesterday_rows:
            parsed = _parse_row_epoch(row, now_epoch)
            if not parsed:
                continue
            app_name, win_title, s_epoch, e_epoch = parsed
            if e_epoch <= yesterday_start_epoch or s_epoch >= yesterday_end_epoch:
                continue
            cs_epoch = max(s_epoch, yesterday_start_epoch)
            ce_epoch = min(e_epoch, yesterday_end_epoch)
            dur = int(ce_epoch - cs_epoch)
            if dur <= 0:
                continue
            yesterday_sessions.append(TimelineSession(
                app_name=app_name,
                window_title=win_title,
                start_time=datetime.fromtimestamp(cs_epoch, tz),
                end_time=datetime.fromtimestamp(ce_epoch, tz),
                duration_seconds=dur,
            ))

        grouped_yesterday = merge_consecutive_sessions(yesterday_sessions)
        switches_today = max(0, len(grouped_sessions) - 1)
        switches_yesterday = max(0, len(grouped_yesterday) - 1) if grouped_yesterday else None

        usage_distribution = [
            AppUsageSummary(app_name=name, duration_seconds=dur)
            for name, dur in sorted(app_durations.items(), key=lambda x: -x[1])
            if dur >= self._MIN_MEANINGFUL_APP_SECONDS
        ]

        total_active_hours = round(total_duration_today / 3600.0, 1)
        longest_focus_period_seconds = longest_session_duration

        category_durations: dict[str, int] = {
            "Development": 0, "Browsers": 0, "Communication": 0,
            "Music": 0, "System": 0, "Utilities": 0, "Other": 0,
        }
        for name, dur in app_durations.items():
            cat = _get_app_category(name)
            category_durations[cat] += dur

        category_breakdown = []
        for cat, dur in category_durations.items():
            if dur > 0:
                pct = int((dur / total_duration_today) * 100) if total_duration_today > 0 else 0
                category_breakdown.append((cat, dur, pct))
        category_breakdown.sort(key=lambda x: -x[1])

        return InsightsData(
            most_used_app_name=most_used_app_name,
            most_used_app_duration=most_used_app_duration,
            most_used_app_percentage=most_used_app_percentage,
            peak_hour_start=peak_hour_start,
            peak_hour_duration=peak_hour_duration,
            longest_session_app=longest_session_app,
            longest_session_duration=longest_session_duration,
            switches_today=switches_today,
            switches_yesterday=switches_yesterday,
            usage_distribution=usage_distribution,
            hourly_activity=hourly_activity,
            total_sessions_today=total_sessions_today,
            avg_session_length_seconds=avg_session_length_seconds,
            most_active_app=most_used_app_name,
            total_active_hours=total_active_hours,
            longest_focus_period_seconds=longest_focus_period_seconds,
            category_breakdown=category_breakdown,
        )

    def load_reports_data(self, *, days: int = 7, start_date: date | None = None, end_date: date | None = None) -> ReportsData | None:
        """Compute analytics for the Reports page over a date range."""
        if not self._database_path.exists():
            return None

        cache_key = f"reports_{days}_{start_date}_{end_date}"
        cached = self._get_query_cache(cache_key)
        if cached is not None:
            return cached

        now = now_utc()
        now_epoch = now.timestamp()
        local_now = now.astimezone()
        today_local = local_now.date()

        if start_date is not None and end_date is not None:
            range_start_local = start_date
            range_end_local = end_date
        else:
            range_end_local = today_local
            range_start_local = today_local - timedelta(days=max(days - 1, 0))

        tz = local_now.tzinfo
        day_bounds = []
        num_days = (range_end_local - range_start_local).days + 1
        for offset in range(num_days):
            d = range_start_local + timedelta(days=offset)
            s_dt = datetime.combine(d, time.min, tzinfo=tz)
            e_dt = s_dt + timedelta(days=1)
            lbl = d.strftime("%a\n%d") if num_days <= 7 else d.strftime("%d/%m")
            day_bounds.append((s_dt.timestamp(), e_dt.timestamp(), d, lbl))

        range_start_epoch = day_bounds[0][0]
        range_end_epoch = day_bounds[-1][1]

        range_start_sql = datetime.fromtimestamp(range_start_epoch, timezone.utc).isoformat().replace("+00:00", "Z")
        range_end_sql = datetime.fromtimestamp(range_end_epoch, timezone.utc).isoformat().replace("+00:00", "Z")
        now_sql = now.isoformat().replace("+00:00", "Z")

        try:
            with sqlite3.connect(self._database_path, timeout=2.0) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT app_name, window_title, start_time, end_time, duration_seconds
                    FROM app_sessions
                    WHERE start_time < ?
                      AND COALESCE(end_time, ?) > ?
                    ORDER BY start_time ASC
                    """,
                    (range_end_sql, now_sql, range_start_sql),
                ).fetchall()
        except sqlite3.Error:
            return None

        day_intervals = [[] for _ in range(num_days)]
        all_intervals_by_app: dict[str, list[tuple[float, float]]] = {}
        all_intervals_flat: list[tuple[float, float]] = []
        parsed_session_count = 0

        for row in rows:
            parsed = _parse_row_epoch(row, now_epoch)
            if not parsed:
                continue
            app_name, _, s_epoch, e_epoch = parsed
            if e_epoch <= range_start_epoch or s_epoch >= range_end_epoch:
                continue

            cs = max(s_epoch, range_start_epoch)
            ce = min(e_epoch, range_end_epoch)
            all_intervals_by_app.setdefault(app_name, []).append((cs, ce))
            all_intervals_flat.append((cs, ce))
            parsed_session_count += 1

            start_idx = max(0, min(int((s_epoch - range_start_epoch) // 86400), num_days - 1))
            end_idx = max(0, min(int((e_epoch - range_start_epoch) // 86400) + 1, num_days))
            for i in range(start_idx, end_idx):
                ds, de, _, _ = day_bounds[i]
                if e_epoch > ds and s_epoch < de:
                    day_intervals[i].append((max(s_epoch, ds), min(e_epoch, de)))

        daily_usage = [
            DailyUsageSummary(
                day=d,
                label=lbl,
                duration_seconds=_merge_float_intervals(day_intervals[i]),
            )
            for i, (ds, de, d, lbl) in enumerate(day_bounds)
        ]

        total_screen_time = _merge_float_intervals(all_intervals_flat)

        app_durations = {
            name: _merge_float_intervals(ivs)
            for name, ivs in all_intervals_by_app.items()
        }
        app_usage = [
            AppUsageSummary(app_name=name, duration_seconds=dur)
            for name, dur in sorted(app_durations.items(), key=lambda x: -x[1])
            if dur >= self._MIN_MEANINGFUL_APP_SECONDS
        ]

        most_used_app_name = app_usage[0].app_name if app_usage else "—"
        most_used_app_duration = app_usage[0].duration_seconds if app_usage else 0

        if daily_usage:
            most_active = max(daily_usage, key=lambda d: d.duration_seconds)
            most_active_day_label = most_active.day.strftime("%A, %b %d")
            most_active_day_seconds = most_active.duration_seconds
        else:
            most_active_day_label = "—"
            most_active_day_seconds = 0

        total_duration = sum(app_durations.values()) or 1
        category_durations: dict[str, int] = {
            "Development": 0, "Browsers": 0, "Communication": 0,
            "Music": 0, "System": 0, "Utilities": 0, "Other": 0,
        }
        for name, dur in app_durations.items():
            cat = _get_app_category(name)
            category_durations[cat] += dur

        category_breakdown = []
        for cat, dur in category_durations.items():
            if dur > 0:
                pct = int((dur / total_duration) * 100)
                category_breakdown.append((cat, dur, pct))
        category_breakdown.sort(key=lambda x: -x[1])

        result = ReportsData(
            total_screen_time_seconds=total_screen_time,
            total_sessions=parsed_session_count,
            most_used_app_name=most_used_app_name,
            most_used_app_duration=most_used_app_duration,
            most_active_day_label=most_active_day_label,
            most_active_day_seconds=most_active_day_seconds,
            daily_usage=daily_usage,
            app_usage=app_usage,
            category_breakdown=category_breakdown,
        )
        self._set_query_cache(cache_key, result)
        return result

    def get_database_stats(self) -> dict[str, Any]:
        """Return raw metrics about the database for the Settings Data page."""
        if not self._database_path.exists():
            return {
                "size_bytes": 0,
                "total_sessions": 0,
                "earliest_date": None,
                "latest_date": None,
            }

        size_bytes = self._database_path.stat().st_size

        try:
            with sqlite3.connect(self._database_path, timeout=2.0) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    """
                    SELECT
                        COUNT(*) AS total_count,
                        MIN(start_time) AS min_start,
                        MAX(COALESCE(end_time, start_time)) AS max_end
                    FROM app_sessions
                    """
                ).fetchone()

                if not row:
                    return {
                        "size_bytes": size_bytes,
                        "total_sessions": 0,
                        "earliest_date": None,
                        "latest_date": None,
                    }

                total_sessions = row["total_count"] or 0
                earliest_raw = row["min_start"]
                latest_raw = row["max_end"]

                earliest_dt = parse_timestamp(earliest_raw) if earliest_raw else None
                latest_dt = parse_timestamp(latest_raw) if latest_raw else None

                return {
                    "size_bytes": size_bytes,
                    "total_sessions": total_sessions,
                    "earliest_date": earliest_dt.date() if earliest_dt else None,
                    "latest_date": latest_dt.date() if latest_dt else None,
                }
        except sqlite3.Error:
            return {
                "size_bytes": size_bytes,
                "total_sessions": 0,
                "earliest_date": None,
                "latest_date": None,
            }

    def get_all_detected_applications(self) -> list[str]:
        """Fetch all unique application names recorded in the database."""
        if not self._database_path.exists():
            return []

        cached = self._get_query_cache("all_detected_apps", ttl=5.0)
        if cached is not None:
            return cached

        try:
            with sqlite3.connect(self._database_path, timeout=2.0) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    """
                    SELECT DISTINCT app_name, window_title
                    FROM app_sessions
                    ORDER BY app_name ASC
                    """
                ).fetchall()

                apps = set()
                for row in rows:
                    raw_app = str(row["app_name"] or "")
                    win_title = str(row["window_title"] or "")
                    norm = normalize_app_name(raw_app, win_title)
                    if norm and norm != "Unknown":
                        apps.add(norm)
                result = sorted(apps, key=lambda s: s.lower())
                self._set_query_cache("all_detected_apps", result)
                return result
        except sqlite3.Error:
            return []

    def reset_all(self) -> None:
        """Wipe all tracking data from the database completely."""
        if not self._database_path.exists():
            return
        try:
            conn = sqlite3.connect(self._database_path, timeout=5.0, isolation_level=None)
            try:
                conn.execute("DELETE FROM app_sessions")
                conn.execute("VACUUM")
            finally:
                conn.close()
            self._query_cache.clear()
        except sqlite3.Error:
            pass

    def reset_today(self, start_of_day_utc: datetime) -> None:
        """Delete all tracking data recorded for today."""
        if not self._database_path.exists():
            return
        iso_str = start_of_day_utc.isoformat()
        try:
            conn = sqlite3.connect(self._database_path, timeout=5.0, isolation_level=None)
            try:
                conn.execute(
                    """
                    DELETE FROM app_sessions
                    WHERE start_time >= ? OR (end_time IS NOT NULL AND end_time >= ?)
                    """,
                    (iso_str, iso_str),
                )
                conn.execute("VACUUM")
            finally:
                conn.close()
            self._query_cache.clear()
        except sqlite3.Error:
            pass
