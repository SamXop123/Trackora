"""Read-only dashboard queries over the Trackora SQLite database."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path

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


class DashboardRepository:
    """Load dashboard-friendly summaries from the Trackora database."""

    _MIN_MEANINGFUL_APP_SECONDS = 10

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path.expanduser()

    def load_snapshot(self) -> DashboardSnapshot:
        """Build a full dashboard snapshot from persisted session rows."""
        if not self._database_path.exists():
            return DashboardSnapshot.empty(
                status_message=f"Database not found: {self._database_path}"
            )

        now = now_utc()
        local_now = now.astimezone()
        today_local = local_now.date()
        yesterday_local = today_local - timedelta(days=1)
        week_start_local = today_local - timedelta(days=6)
        day_start_utc, day_end_utc = self._local_day_bounds(today_local, local_now)
        yesterday_start_utc, yesterday_end_utc = self._local_day_bounds(
            yesterday_local,
            local_now,
        )
        week_start_utc, _ = self._local_day_bounds(week_start_local, local_now)

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
                    """
                    ,
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

        sessions = [self._to_session_record(row) for row in session_rows]
        todays_sessions = [
            session
            for session in sessions
            if self._intersects_day(session, day_start_utc, day_end_utc, now)
        ]
        yesterdays_sessions = [
            session
            for session in sessions
            if self._intersects_day(session, yesterday_start_utc, yesterday_end_utc, now)
        ]
        normalized_sessions = self._normalized_sessions(
            todays_sessions=todays_sessions,
            day_start_utc=day_start_utc,
            day_end_utc=day_end_utc,
            now=now,
        )
        normalized_yesterday = self._normalized_sessions(
            todays_sessions=yesterdays_sessions,
            day_start_utc=yesterday_start_utc,
            day_end_utc=yesterday_end_utc,
            now=now,
        )
        weekly_days = self._build_weekly_daily_totals(
            sessions=sessions,
            start_day=week_start_local,
            local_now=local_now,
            now=now,
        )

        top_apps = self._aggregate_app_usage(
            normalized_sessions=normalized_sessions,
            day_start_utc=day_start_utc,
            day_end_utc=day_end_utc,
        )
        meaningful_apps = self._filter_meaningful_app_usage(top_apps)
        hourly_seconds = self._build_hourly_buckets(
            normalized_sessions=normalized_sessions,
            today_local=today_local,
            tzinfo=local_now.tzinfo,
            now=now,
        )
        active_app = self._active_app_status(active_row, now)
        total_seconds = self._merged_total_seconds(normalized_sessions)
        total_yesterday_seconds = self._merged_total_seconds(normalized_yesterday)
        total_last7days_seconds = sum(day.duration_seconds for day in weekly_days)
        return DashboardSnapshot(
            total_today_seconds=total_seconds,
            total_yesterday_seconds=total_yesterday_seconds,
            total_last7days_seconds=total_last7days_seconds,
            active_app=active_app,
            top_apps=meaningful_apps[:5],
            all_apps=meaningful_apps,
            hourly_labels=[f"{hour:02d}" for hour in range(24)],
            hourly_values=[round(seconds / 3600, 2) for seconds in hourly_seconds],
            weekly_labels=[day.label for day in weekly_days],
            weekly_values=[round(day.duration_seconds / 3600, 2) for day in weekly_days],
            weekly_days=weekly_days,
            last_refreshed=local_now,
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
        local_now = now.astimezone()
        today_local = local_now.date()
        day_start_utc, day_end_utc = self._local_day_bounds(today_local, local_now)

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
        for row in rows:
            start = parse_timestamp(str(row["start_time"] or ""))
            if start is None:
                continue
            end_raw = str(row["end_time"] or "") if row["end_time"] else None
            end = parse_timestamp(end_raw) if end_raw else now
            if end <= start:
                continue
            # Clip to today's bounds
            clipped_start = max(start, day_start_utc)
            clipped_end = min(end, day_end_utc)
            if clipped_end <= clipped_start:
                continue
            dur = duration_seconds(clipped_start, clipped_end)
            app_name = normalize_app_name(
                str(row["app_name"] or "Unknown"),
                str(row["window_title"] or ""),
            )
            sessions.append(TimelineSession(
                app_name=app_name,
                window_title=str(row["window_title"] or ""),
                start_time=clipped_start,
                end_time=clipped_end,
                duration_seconds=dur,
            ))
        return sessions

    def load_app_details(self, *, days: int = 1) -> list[AppDetailedStats]:
        """Per-app stats for the Applications page over a given day range."""
        if not self._database_path.exists():
            return []

        now = now_utc()
        local_now = now.astimezone()
        today_local = local_now.date()
        range_start_local = today_local - timedelta(days=max(days - 1, 0))
        range_start_utc, _ = self._local_day_bounds(range_start_local, local_now)
        _, range_end_utc = self._local_day_bounds(today_local, local_now)

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

        sessions = [self._to_session_record(row) for row in rows]
        relevant = [
            s for s in sessions
            if self._intersects_day(s, range_start_utc, range_end_utc, now)
        ]
        normalized = self._normalized_sessions(
            todays_sessions=relevant,
            day_start_utc=range_start_utc,
            day_end_utc=range_end_utc,
            now=now,
        )

        # Group by app: intervals and session count
        app_intervals: dict[str, list[tuple[datetime, datetime]]] = {}
        app_session_counts: dict[str, int] = {}
        app_last_active: dict[str, datetime] = {}
        for app_name, start, end in normalized:
            app_intervals.setdefault(app_name, []).append((start, end))
            app_session_counts[app_name] = app_session_counts.get(app_name, 0) + 1
            prev = app_last_active.get(app_name)
            if prev is None or end > prev:
                app_last_active[app_name] = end

        results: list[AppDetailedStats] = []
        for app_name, intervals in app_intervals.items():
            total = self._merged_intervals_seconds(intervals)
            if total < self._MIN_MEANINGFUL_APP_SECONDS:
                continue
            count = app_session_counts[app_name]
            results.append(AppDetailedStats(
                app_name=app_name,
                duration_seconds=total,
                session_count=count,
                avg_session_seconds=total // max(count, 1),
                last_active=app_last_active.get(app_name),
            ))
        results.sort(key=lambda x: (-x.duration_seconds, x.app_name.lower()))
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
        end = parse_timestamp(session.end_time) if session.end_time else now
        return end > day_start_utc and start < day_end_utc

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
        """
        Hide tiny app totals from the dashboard while keeping them in SQLite.

        This keeps "Top Apps Today" focused on meaningful usage without altering
        the underlying recorded session history.
        """
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

        # Check for staleness using the last_heartbeat_time if available
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

        return ActiveAppStatus(
            app_name=normalize_app_name(
                str(active_row["app_name"] or "Unknown"),
                str(active_row["window_title"] or ""),
            ),
            window_title=str(active_row["window_title"] or ""),
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
        """
        Normalize session intervals for dashboard calculations.

        Bad historical data can contain overlaps or reversed times. We clip
        everything to today's bounds and discard invalid ranges so daily totals
        stay realistic.
        """
        normalized: list[tuple[str, datetime, datetime]] = []
        for session in todays_sessions:
            start = parse_timestamp(session.start_time)
            if start is None:
                continue
            end = parse_timestamp(session.end_time) if session.end_time else now
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
        """Calculate productivity insights based on today's and yesterday's telemetry."""
        if not self._database_path.exists():
            return None

        now = now_utc()
        local_now = now.astimezone()
        today_local = local_now.date()
        yesterday_local = today_local - timedelta(days=1)
        day_start_utc, day_end_utc = self._local_day_bounds(today_local, local_now)
        yesterday_start_utc, yesterday_end_utc = self._local_day_bounds(yesterday_local, local_now)

        try:
            with sqlite3.connect(self._database_path, timeout=2.0) as conn:
                conn.row_factory = sqlite3.Row
                
                # Today's sessions
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

                # Yesterday's sessions (to calculate accurate grouped switches yesterday)
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

        # Process today's raw sessions
        sessions: list[TimelineSession] = []
        for row in today_rows:
            start = parse_timestamp(str(row["start_time"] or ""))
            if start is None:
                continue
            end_raw = str(row["end_time"] or "") if row["end_time"] else None
            end = parse_timestamp(end_raw) if end_raw else now
            if end <= start:
                continue
            
            # Clip to today's bounds
            clipped_start = max(start, day_start_utc)
            clipped_end = min(end, day_end_utc)
            if clipped_end <= clipped_start:
                continue
            
            dur = duration_seconds(clipped_start, clipped_end)
            app_name = normalize_app_name(
                str(row["app_name"] or "Unknown"),
                str(row["window_title"] or ""),
            )
            sessions.append(TimelineSession(
                app_name=app_name,
                window_title=str(row["window_title"] or ""),
                start_time=clipped_start,
                end_time=clipped_end,
                duration_seconds=dur,
            ))

        if not sessions:
            return None

        # Apply Central Grouping Engine for Today
        grouped_sessions = merge_consecutive_sessions(sessions)
        if not grouped_sessions:
            return None

        # 1. Total sessions today (actual app switches)
        total_sessions_today = len(grouped_sessions)

        # 2. Avg session length on grouped sessions
        avg_session_length_seconds = int(sum(s.duration_seconds for s in grouped_sessions) / len(grouped_sessions))

        # 3. App usage durations
        app_durations: dict[str, int] = {}
        for s in grouped_sessions:
            app_durations[s.app_name] = app_durations.get(s.app_name, 0) + s.duration_seconds

        total_duration_today = sum(app_durations.values())

        # 4. Most Used App
        most_used_app_name = max(app_durations, key=app_durations.get) if app_durations else ""
        most_used_app_duration = app_durations[most_used_app_name] if most_used_app_name else 0
        most_used_app_percentage = int((most_used_app_duration / total_duration_today) * 100) if total_duration_today > 0 else 0

        # 5. Peak hour range and duration (using raw sessions to maintain high-fidelity timing)
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

        # 6. Longest session on grouped sessions
        longest_s = max(grouped_sessions, key=lambda s: s.duration_seconds)
        longest_session_app = longest_s.app_name
        longest_session_duration = longest_s.duration_seconds

        # 7. App switches comparisons (using grouped sessions for yesterday)
        yesterday_sessions: list[TimelineSession] = []
        for row in yesterday_rows:
            start = parse_timestamp(str(row["start_time"] or ""))
            if start is None:
                continue
            end_raw = str(row["end_time"] or "") if row["end_time"] else None
            end = parse_timestamp(end_raw) if end_raw else now
            if end <= start:
                continue
            clipped_start = max(start, yesterday_start_utc)
            clipped_end = min(end, yesterday_end_utc)
            if clipped_end <= clipped_start:
                continue
            dur = duration_seconds(clipped_start, clipped_end)
            app_name = normalize_app_name(
                str(row["app_name"] or "Unknown"),
                str(row["window_title"] or ""),
            )
            yesterday_sessions.append(TimelineSession(
                app_name=app_name,
                window_title=str(row["window_title"] or ""),
                start_time=clipped_start,
                end_time=clipped_end,
                duration_seconds=dur,
            ))
        grouped_yesterday = merge_consecutive_sessions(yesterday_sessions)

        switches_today = total_sessions_today
        switches_yesterday = len(grouped_yesterday) if grouped_yesterday else None

        # 8. Usage distribution
        usage_distribution = [
            AppUsageSummary(app_name=name, duration_seconds=dur)
            for name, dur in sorted(app_durations.items(), key=lambda x: -x[1])
        ]

        # 9. Total active hours
        total_active_hours = round(total_duration_today / 3600.0, 1)

        # 10. Longest focus period is precisely the longest session from grouped sessions
        longest_focus_period_seconds = longest_session_duration

        # 11. Category Breakdown
        category_durations: dict[str, int] = {
            "Development": 0,
            "Browsers": 0,
            "Communication": 0,
            "Music": 0,
            "System": 0,
            "Utilities": 0,
            "Other": 0,
        }
        for name, dur in app_durations.items():
            name_lower = name.lower()
            if any(keyword in name_lower for keyword in ["vs code", "vscode", "cursor", "kitty", "terminal", "console", "sublime", "pycharm", "webstorm", "intellij", "git", "github", "neovim", "vim", "emacs", "bash", "sh", "antigravity"]):
                cat = "Development"
            elif any(keyword in name_lower for keyword in ["chrome", "chromium", "firefox", "brave", "safari", "edge", "opera", "vivaldi", "browser"]):
                cat = "Browsers"
            elif any(keyword in name_lower for keyword in ["discord", "slack", "telegram", "teams", "zoom", "skype", "whatsapp", "signal", "messenger", "wechat", "mail", "outlook", "thunderbird"]):
                cat = "Communication"
            elif any(keyword in name_lower for keyword in ["spotify", "rhythmbox", "vlc", "audacious", "clementine", "itunes", "music", "youtube music", "deezer"]):
                cat = "Music"
            elif any(keyword in name_lower for keyword in ["settings", "system settings", "gnome-control-center", "task manager", "monitor", "finder", "nautilus", "files", "explorer", "dbus", "xorg", "software", "gnome-software"]):
                cat = "System"
            elif any(keyword in name_lower for keyword in ["calculator", "text editor", "notes", "obsidian", "notion", "keep", "gedit", "kwrite", "archive", "file roller", "manager"]):
                cat = "Utilities"
            else:
                cat = "Other"
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
        """Compute analytics for the Reports page over a date range.

        Args:
            days: Number of days to look back (used when start_date/end_date not specified).
            start_date: Explicit start of date range (inclusive).
            end_date: Explicit end of date range (inclusive).
        """
        if not self._database_path.exists():
            return None

        now = now_utc()
        local_now = now.astimezone()
        today_local = local_now.date()

        if start_date is not None and end_date is not None:
            range_start_local = start_date
            range_end_local = end_date
        else:
            range_end_local = today_local
            range_start_local = today_local - timedelta(days=max(days - 1, 0))

        range_start_utc, _ = self._local_day_bounds(range_start_local, local_now)
        _, range_end_utc = self._local_day_bounds(range_end_local, local_now)

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
            return None

        sessions = [self._to_session_record(row) for row in rows]

        # Build daily summaries
        num_days = (range_end_local - range_start_local).days + 1
        daily_usage: list[DailyUsageSummary] = []
        for offset in range(num_days):
            day = range_start_local + timedelta(days=offset)
            day_start_utc, day_end_utc = self._local_day_bounds(day, local_now)
            day_sessions = [
                s for s in sessions
                if self._intersects_day(s, day_start_utc, day_end_utc, now)
            ]
            normalized = self._normalized_sessions(
                todays_sessions=day_sessions,
                day_start_utc=day_start_utc,
                day_end_utc=day_end_utc,
                now=now,
            )
            daily_usage.append(DailyUsageSummary(
                day=day,
                label=day.strftime("%a\n%d") if num_days <= 7 else day.strftime("%d/%m"),
                duration_seconds=self._merged_total_seconds(normalized),
            ))

        # Full range aggregation
        relevant = [
            s for s in sessions
            if self._intersects_day(s, range_start_utc, range_end_utc, now)
        ]
        normalized_all = self._normalized_sessions(
            todays_sessions=relevant,
            day_start_utc=range_start_utc,
            day_end_utc=range_end_utc,
            now=now,
        )

        total_screen_time = self._merged_total_seconds(normalized_all)

        # Build TimelineSessions for grouping engine
        tl_sessions: list[TimelineSession] = []
        for app_name, start, end in normalized_all:
            dur = duration_seconds(start, end)
            tl_sessions.append(TimelineSession(
                app_name=app_name,
                window_title="",
                start_time=start,
                end_time=end,
                duration_seconds=dur,
            ))

        grouped = merge_consecutive_sessions(tl_sessions)
        total_sessions = len(grouped)

        # App usage
        app_durations: dict[str, int] = {}
        for s in grouped:
            app_durations[s.app_name] = app_durations.get(s.app_name, 0) + s.duration_seconds

        app_usage = [
            AppUsageSummary(app_name=name, duration_seconds=dur)
            for name, dur in sorted(app_durations.items(), key=lambda x: -x[1])
        ]

        most_used_app_name = app_usage[0].app_name if app_usage else "—"
        most_used_app_duration = app_usage[0].duration_seconds if app_usage else 0

        # Most active day
        if daily_usage:
            most_active = max(daily_usage, key=lambda d: d.duration_seconds)
            most_active_day_label = most_active.day.strftime("%A, %b %d")
            most_active_day_seconds = most_active.duration_seconds
        else:
            most_active_day_label = "—"
            most_active_day_seconds = 0

        # Category breakdown
        total_duration = sum(app_durations.values()) or 1
        category_durations: dict[str, int] = {
            "Development": 0, "Browsers": 0, "Communication": 0,
            "Music": 0, "System": 0, "Utilities": 0, "Other": 0,
        }
        for name, dur in app_durations.items():
            name_lower = name.lower()
            if any(kw in name_lower for kw in ["vs code", "vscode", "cursor", "kitty", "terminal", "console", "sublime", "pycharm", "webstorm", "intellij", "git", "github", "neovim", "vim", "emacs", "bash", "sh", "antigravity"]):
                cat = "Development"
            elif any(kw in name_lower for kw in ["chrome", "chromium", "firefox", "brave", "safari", "edge", "opera", "vivaldi", "browser"]):
                cat = "Browsers"
            elif any(kw in name_lower for kw in ["discord", "slack", "telegram", "teams", "zoom", "skype", "whatsapp", "signal", "messenger", "wechat", "mail", "outlook", "thunderbird"]):
                cat = "Communication"
            elif any(kw in name_lower for kw in ["spotify", "rhythmbox", "vlc", "audacious", "clementine", "itunes", "music", "youtube music", "deezer"]):
                cat = "Music"
            elif any(kw in name_lower for kw in ["settings", "system settings", "gnome-control-center", "task manager", "monitor", "finder", "nautilus", "files", "explorer", "dbus", "xorg", "software", "gnome-software"]):
                cat = "System"
            elif any(kw in name_lower for kw in ["calculator", "text editor", "notes", "obsidian", "notion", "keep", "gedit", "kwrite", "archive", "file roller", "manager"]):
                cat = "Utilities"
            else:
                cat = "Other"
            category_durations[cat] += dur

        category_breakdown = []
        for cat, dur in category_durations.items():
            if dur > 0:
                pct = int((dur / total_duration) * 100)
                category_breakdown.append((cat, dur, pct))
        category_breakdown.sort(key=lambda x: -x[1])

        return ReportsData(
            total_screen_time_seconds=total_screen_time,
            total_sessions=total_sessions,
            most_used_app_name=most_used_app_name,
            most_used_app_duration=most_used_app_duration,
            most_active_day_label=most_active_day_label,
            most_active_day_seconds=most_active_day_seconds,
            daily_usage=daily_usage,
            app_usage=app_usage,
            category_breakdown=category_breakdown,
        )
