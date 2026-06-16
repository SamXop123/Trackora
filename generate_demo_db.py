#!/usr/bin/env python3
"""Generate a realistic, populated Trackora SQLite database for demoing and screenshots."""

from __future__ import annotations

import sqlite3
import random
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Define realistic developer apps and associated window titles
APPS_POOL = {
    "VS Code": [
        "generate_demo_db.py - Trackora - Visual Studio Code",
        "index.css - Trackora - Visual Studio Code",
        "app.py - Trackora - Visual Studio Code",
        "sqlite.py - Trackora - Visual Studio Code",
        "settings.py - Trackora - Visual Studio Code",
        "dashboard_window.py - Trackora - Visual Studio Code",
        "README.md - Trackora - Visual Studio Code",
        "install.sh - Trackora - Visual Studio Code",
    ],
    "Brave": [
        "PySide6 QDialog Custom Styles - Google Search - Brave",
        "sqlite3 — DB-API 2.0 interface — Python 3.12 documentation - Brave",
        "GitHub - SamXop123/Trackora: Premium screen time tracker - Brave",
        "Stack Overflow - How to implement rollback in shell scripts - Brave",
        "GNOME Shell Extension Developer Documentation - Brave",
        "Fedora User Guide & Package Manager docs - Brave",
    ],
    "Chrome": [
        "Trello Board - Trackora Project - Google Chrome",
        "Google Calendar - June 2026 - Google Chrome",
        "ChatGPT - Code Review Assistant - Google Chrome",
        "Tailwind CSS Cheat Sheet - Google Chrome",
    ],
    "Terminal": [
        "sam@fedora: ~/dev-work/Trackora",
        "sam@fedora: ~/dev-work/Trackora (npm run dev)",
        "sam@fedora: ~/dev-work/Trackora (git status)",
        "sam@fedora: ~/dev-work/Trackora (journalctl -xe)",
        "sam@fedora: ~ (htop)",
    ],
    "Spotify": [
        "Spotify Free",
        "Lo-Fi Coding Beats - playlist by Spotify",
        "Synthwave Radio - Spotify",
        "Chilled Cow - Spotify",
    ],
    "Discord": [
        "#development - Trackora Discord Server",
        "#announcements - GNOME Extensions Server",
        "Direct Messages - dot_notsam",
    ],
    "Obsidian": [
        "Trackora Design Specs - Obsidian v1.5",
        "Daily Log 2026-06-16 - Obsidian v1.5",
        "Brainstorming Session Notes - Obsidian v1.5",
    ],
    "GitKraken": [
        "Trackora [main] - GitKraken",
        "Trackora [feature/service-checks] - GitKraken",
    ],
}


def to_utc_iso(dt: datetime) -> str:
    """Format datetime for sqlite storage as UTC ISO timestamp."""
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def generate_demo_database(db_path: Path, days: int = 30) -> None:
    """Populate a demo database with realistic software developer usage patterns."""
    if db_path.exists():
        db_path.unlink()

    # Initialize SQLite database with matching schema
    conn = sqlite3.connect(db_path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS app_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_name TEXT NOT NULL,
                window_title TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_seconds INTEGER CHECK (duration_seconds IS NULL OR duration_seconds >= 0),
                last_heartbeat_time TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_app_sessions_single_open
            ON app_sessions ((1))
            WHERE end_time IS NULL
            """
        )

    print(f"[INFO] Seeding {days} days of developer activity data...")

    end_time_anchor = datetime.now(timezone.utc)
    start_time_anchor = end_time_anchor - timedelta(days=days)

    current_dt = start_time_anchor

    total_sessions = 0

    while current_dt < end_time_anchor:
        is_weekend = current_dt.weekday() >= 5
        
        # Decide daily working blocks
        blocks = []
        if is_weekend:
            # Weekends: Light personal projects or browsing
            if random.random() < 0.7:  # 70% chance of using computer on weekend
                start_hour = random.randint(10, 15)
                duration_hours = random.uniform(1.0, 3.5)
                blocks.append((start_hour, duration_hours))
        else:
            # Weekdays: Productive developer work day
            # Block 1: Morning Focus (e.g. 9:00 AM - 12:30 PM)
            blocks.append((9 + random.uniform(-0.5, 0.5), random.uniform(3.0, 4.0)))
            # Block 2: Afternoon Coding (e.g. 1:30 PM - 5:30 PM)
            blocks.append((13.5 + random.uniform(-0.3, 0.5), random.uniform(3.5, 4.5)))
            # Block 3: Night Hacking (35% chance, e.g. 8:30 PM - 11:00 PM)
            if random.random() < 0.35:
                blocks.append((20.5 + random.uniform(-0.5, 0.5), random.uniform(1.5, 3.0)))

        for start_hour, duration_hours in blocks:
            block_start = current_dt.replace(
                hour=int(start_hour),
                minute=int((start_hour % 1) * 60),
                second=0,
                microsecond=0,
            )
            block_end = block_start + timedelta(hours=duration_hours)
            
            # Populate sessions sequentially within the block
            session_dt = block_start
            
            while session_dt < block_end:
                # App switching weights (heavily favoring VS Code, Terminal, Browsers)
                if is_weekend:
                    app_weights = {
                        "VS Code": 0.20,
                        "Brave": 0.35,
                        "Chrome": 0.15,
                        "Terminal": 0.10,
                        "Spotify": 0.10,
                        "Discord": 0.10,
                        "Obsidian": 0.0,
                        "GitKraken": 0.0,
                    }
                else:
                    app_weights = {
                        "VS Code": 0.40,
                        "Terminal": 0.18,
                        "Brave": 0.15,
                        "Chrome": 0.07,
                        "GitKraken": 0.05,
                        "Discord": 0.05,
                        "Obsidian": 0.05,
                        "Spotify": 0.05,
                    }

                apps = list(app_weights.keys())
                weights = list(app_weights.values())
                chosen_app = random.choices(apps, weights=weights, k=1)[0]
                
                # Determine realistic durations per app
                if chosen_app == "VS Code":
                    duration = random.randint(180, 2400)  # 3 to 40 minutes
                elif chosen_app in ("Brave", "Chrome"):
                    duration = random.randint(60, 900)   # 1 to 15 minutes
                elif chosen_app == "Terminal":
                    duration = random.randint(30, 360)   # 30s to 6 minutes
                elif chosen_app == "GitKraken":
                    duration = random.randint(30, 180)   # 30s to 3 minutes
                elif chosen_app in ("Discord", "Spotify"):
                    duration = random.randint(20, 180)   # Quick song change or chat
                else:
                    duration = random.randint(60, 600)   # Obsidian writing notes

                # Avoid running past the work block end
                if session_dt + timedelta(seconds=duration) > block_end:
                    duration = int((block_end - session_dt).total_seconds())
                
                if duration < 5:
                    break

                window_title = random.choice(APPS_POOL[chosen_app])
                start_iso = to_utc_iso(session_dt)
                end_dt = session_dt + timedelta(seconds=duration)
                end_iso = to_utc_iso(end_dt)

                with conn:
                    conn.execute(
                        """
                        INSERT INTO app_sessions (
                            app_name, window_title, start_time, end_time, duration_seconds, last_heartbeat_time
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (chosen_app, window_title, start_iso, end_iso, duration, end_iso)
                    )

                total_sessions += 1
                
                # Small gap for idle / context switching (0 to 30 seconds)
                gap = random.randint(0, 30)
                session_dt = end_dt + timedelta(seconds=gap)

        current_dt += timedelta(days=1)

    # Insert an active session at the very end to show "Currently Active" status in the UI
    # We set last_heartbeat_time to 1 year in the future so that it never goes stale when previewing
    active_start_dt = end_time_anchor - timedelta(minutes=2, seconds=15)
    active_start_iso = to_utc_iso(active_start_dt)
    active_heartbeat_iso = to_utc_iso(end_time_anchor + timedelta(days=365))
    with conn:
        conn.execute(
            """
            INSERT INTO app_sessions (
                app_name, window_title, start_time, end_time, duration_seconds, last_heartbeat_time
            ) VALUES (?, ?, ?, NULL, NULL, ?)
            """,
            ("VS Code", "generate_demo_db.py - Trackora - Visual Studio Code", active_start_iso, active_heartbeat_iso)
        )
    total_sessions += 1

    conn.close()
    print(f"[SUCCESS] Generated {total_sessions} sessions successfully in '{db_path}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a realistic developer activity demo database for Trackora.")
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="demo.db",
        help="Target SQLite database file path (default: demo.db)"
    )
    parser.add_argument(
        "--days",
        "-d",
        type=int,
        default=30,
        help="Number of days of data to generate (default: 30)"
    )
    args = parser.parse_args()

    db_file = Path(args.output).resolve()
    generate_demo_database(db_file, days=args.days)
    print("\nTo use this demo database in the Trackora UI, run:")
    print(f"  python3 -m trackora.gui --database {db_file}")
