"""Settings manager for storing persistent configuration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from datetime import datetime, timedelta, timezone
from trackora.utils.paths import trackora_data_dir
from trackora.utils.app_names import normalize_app_name
from trackora.utils.time import now_utc

__all__ = [
    "SettingsConfig",
    "SettingsManager",
    "settings_manager",
]


@dataclass
class SettingsConfig:
    # General
    start_minimized: bool = False
    desktop_notifications: bool = True
    minimize_to_tray: bool = True
    
    # Tracking
    tracking_interval_seconds: int = 3
    excluded_applications: list[str] = field(default_factory=list)
    paused_until: str | None = None
    
    # Advanced
    enable_debug_logging: bool = False
    show_dev_info: bool = False
    auto_backup_daily: bool = False


class SettingsManager:
    """Manager for loading and saving settings to JSON."""

    def __init__(self, settings_path: Path | None = None) -> None:
        self.path = settings_path or (trackora_data_dir() / "settings.json")
        self.config = SettingsConfig()
        self.load()

    def load(self) -> None:
        """Load settings from disk."""
        if not self.path.exists():
            return
            
        try:
            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                return
                
            # Safely extract known keys
            config_dict = asdict(self.config)
            for k, v in data.items():
                if k in config_dict and isinstance(v, type(config_dict[k])):
                    setattr(self.config, k, v)
        except (OSError, json.JSONDecodeError):
            pass

    def save(self) -> None:
        """Save current settings to disk."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            raw = json.dumps(asdict(self.config), indent=4)
            self.path.write_text(raw, encoding="utf-8")
        except OSError:
            pass

    # Convenience accessors
    def get(self, key: str) -> Any:
        return getattr(self.config, key)

    def set(self, key: str, value: Any) -> None:
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            self.save()

    def get_excluded_applications(self) -> list[str]:
        return list(self.config.excluded_applications)

    def add_excluded_application(self, app_name: str) -> None:
        app_clean = app_name.strip()
        if not app_clean:
            return
        if not self.is_application_excluded(app_clean):
            self.config.excluded_applications.append(app_clean)
            self.save()

    def remove_excluded_application(self, app_name: str) -> None:
        app_clean = app_name.strip()
        if not app_clean:
            return
        raw_target = app_clean.casefold()
        norm_target = normalize_app_name(app_clean).casefold()
        
        new_list = []
        for item in self.config.excluded_applications:
            ex_raw = item.strip().casefold()
            ex_norm = normalize_app_name(item).casefold()
            if raw_target == ex_raw or norm_target == ex_raw or raw_target == ex_norm or norm_target == ex_norm:
                continue
            new_list.append(item)
        self.config.excluded_applications = new_list
        self.save()

    def is_application_excluded(self, app_name: str, window_title: str = "") -> bool:
        if not app_name:
            return False
        # Reload latest settings from disk in case GUI updated settings.json
        self.load()
        raw_target = app_name.strip().casefold()
        norm_target = normalize_app_name(app_name, window_title).casefold()
        title_target = (window_title or "").strip().casefold()

        for item in self.config.excluded_applications:
            ex = item.strip().casefold()
            if not ex:
                continue
            ex_norm = normalize_app_name(item).casefold()
            
            # Direct match on raw process name or normalized display app name
            if raw_target == ex or norm_target == ex or raw_target == ex_norm or norm_target == ex_norm:
                return True
                
            # Flexible keyword match for app names or window titles (e.g. "Trackora", "Antigravity")
            if ex in raw_target or ex in norm_target or (len(ex) >= 3 and ex in title_target):
                return True

        return False

    # Pause Tracking
    def pause_tracking(self, minutes: int | None = None) -> None:
        """
        Pause tracking.
        :param minutes: Duration in minutes to pause. If None or <= 0, pause indefinitely until resumed.
        """
        if minutes is None or minutes <= 0:
            self.config.paused_until = "indefinite"
        else:
            until_dt = now_utc() + timedelta(minutes=minutes)
            self.config.paused_until = until_dt.isoformat()
        self.save()

    def resume_tracking(self) -> None:
        """Resume tracking immediately."""
        self.config.paused_until = None
        self.save()

    def is_tracking_paused(self) -> bool:
        """Check if tracking is currently paused (real-time disk sync)."""
        self.load()
        paused = self.config.paused_until
        if not paused:
            return False
        if paused == "indefinite":
            return True
        try:
            until_dt = datetime.fromisoformat(paused)
            if until_dt.tzinfo is None:
                until_dt = until_dt.replace(tzinfo=timezone.utc)
            if now_utc() < until_dt:
                return True
            # Timed pause expired -> auto resume
            self.config.paused_until = None
            self.save()
            return False
        except (ValueError, TypeError):
            self.config.paused_until = None
            self.save()
            return False

    def get_pause_remaining_seconds(self) -> float | None:
        """
        Get remaining pause seconds.
        Returns:
          - None if not paused
          - float('inf') if paused indefinitely
          - positive float of remaining seconds if timed pause
        """
        self.load()
        paused = self.config.paused_until
        if not paused:
            return None
        if paused == "indefinite":
            return float("inf")
        try:
            until_dt = datetime.fromisoformat(paused)
            if until_dt.tzinfo is None:
                until_dt = until_dt.replace(tzinfo=timezone.utc)
            rem = (until_dt - now_utc()).total_seconds()
            if rem > 0:
                return rem
            # Expired
            self.config.paused_until = None
            self.save()
            return None
        except (ValueError, TypeError):
            self.config.paused_until = None
            self.save()
            return None

# Global instance for UI
settings_manager = SettingsManager()
