"""Settings manager for storing persistent configuration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from trackora.utils.paths import trackora_data_dir


@dataclass
class SettingsConfig:
    # General
    start_minimized: bool = False
    desktop_notifications: bool = True
    minimize_to_tray: bool = True
    
    # Tracking
    tracking_interval_seconds: int = 3
    
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

# Global instance for UI
settings_manager = SettingsManager()
