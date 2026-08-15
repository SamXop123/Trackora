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
        self._last_mtime: float = -1.0
        self._cached_excluded_items: list[tuple[str, set[str]]] = []
        self.load(force=True)

    def _rebuild_excluded_cache(self) -> None:
        self._cached_excluded_items = []
        for item in self.config.excluded_applications:
            tokens = self._extract_tokens(item)
            if tokens:
                self._cached_excluded_items.append((item.strip().casefold(), tokens))

    def load(self, force: bool = False) -> None:
        """Load settings from disk only when file has been modified."""
        if not self.path.exists():
            self._rebuild_excluded_cache()
            return
            
        try:
            mtime = self.path.stat().st_mtime
            if not force and self._last_mtime == mtime:
                return
            self._last_mtime = mtime

            raw = self.path.read_text(encoding="utf-8")
            data = json.loads(raw)
            if not isinstance(data, dict):
                self._rebuild_excluded_cache()
                return
                
            # Safely extract known keys
            config_dict = asdict(self.config)
            for k, v in data.items():
                if k in config_dict:
                    current_val = config_dict[k]
                    if current_val is None or v is None or isinstance(v, type(current_val)):
                        setattr(self.config, k, v)
            self._rebuild_excluded_cache()
        except (OSError, json.JSONDecodeError):
            self._rebuild_excluded_cache()

    def save(self) -> None:
        """Save current settings to disk."""
        try:
            self._rebuild_excluded_cache()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            raw = json.dumps(asdict(self.config), indent=4)
            self.path.write_text(raw, encoding="utf-8")
            try:
                self._last_mtime = self.path.stat().st_mtime
            except Exception:
                pass
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
        already = {a.strip().casefold() for a in self.config.excluded_applications}
        if app_clean.casefold() not in already:
            self.config.excluded_applications.append(app_clean)
            self.save()

    def remove_excluded_application(self, app_name: str) -> None:
        app_clean = app_name.strip().casefold()
        if not app_clean:
            return
        new_list = [
            item for item in self.config.excluded_applications
            if item.strip().casefold() != app_clean
        ]
        self.config.excluded_applications = new_list
        self.save()

    @staticmethod
    def _extract_tokens(text: str) -> set[str]:
        """Extract multi-variant tokens from an app name or process name."""
        clean = (text or "").strip().casefold()
        if clean.endswith(".exe"):
            clean = clean[:-4].strip()
        if not clean:
            return set()
        
        tokens = {clean}
        # Alphanumeric collapsed token (e.g. "vs code" -> "vscode", "forza horizon 6" -> "forzahorizon6")
        alnum = "".join(c for c in clean if c.isalnum())
        if alnum:
            tokens.add(alnum)

        # Normalized display name tokens
        norm = normalize_app_name(clean).casefold()
        tokens.add(norm)
        norm_alnum = "".join(c for c in norm if c.isalnum())
        if norm_alnum:
            tokens.add(norm_alnum)

        # Word tokens
        words = [w for w in clean.replace("-", " ").replace("_", " ").replace(".", " ").split() if len(w) >= 3]
        tokens.update(words)
        return tokens

    def is_application_excluded(self, app_name: str, window_title: str = "") -> bool:
        if not app_name or not self._cached_excluded_items:
            return False

        app_tokens = self._extract_tokens(app_name)
        norm_app = normalize_app_name(app_name, window_title).casefold()
        app_tokens.add(norm_app)
        norm_alnum = "".join(c for c in norm_app if c.isalnum())
        if norm_alnum:
            app_tokens.add(norm_alnum)

        title_lower = (window_title or "").strip().casefold()
        is_browser = any(b in app_tokens for b in ("chrome", "msedge", "edge", "firefox", "brave", "opera", "vivaldi", "chromium", "zen"))

        for item_lower, item_tokens in self._cached_excluded_items:
            # 1. Exact token intersection (e.g. "chrome" == "chrome", "vscode" == "vscode", "whatsapp" == "whatsapp")
            if app_tokens & item_tokens:
                return True

            # 2. Token containment on application tokens for terms >= 3 characters
            for it in item_tokens:
                if len(it) < 3:
                    continue
                if any(it in at or at in it for at in app_tokens if len(at) >= 3):
                    return True

            # 3. Window title matching
            for it in item_tokens:
                if len(it) < 3:
                    continue
                if is_browser and it in title_lower:
                    return True
                if title_lower.endswith(f" - {it}") or title_lower.endswith(f" — {it}") or title_lower.endswith(f" | {it}") or title_lower == it:
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
