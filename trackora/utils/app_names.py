"""Display-name normalization for tracked application identifiers."""

from __future__ import annotations


_APP_NAME_MAP = {
    "code": "VS Code",
    "code-oss": "VS Code",
    "google-chrome": "Chrome",
    "chrome": "Chrome",
    "chromium": "Chromium",
    "brave-browser": "Brave",
    "firefox": "Firefox",
    "org.gnome.nautilus": "Files",
    "nautilus": "Files",
    "org.gnome.console": "Console",
    "gnome-console": "Console",
    "org.gnome.settings": "Settings",
    "gnome-control-center": "Settings",
    "kitty": "Kitty",
    "spotify": "Spotify",
    "slack": "Slack",
    "discord": "Discord",
    "telegram-desktop": "Telegram",
}


def normalize_app_name(app_name: str, window_title: str = "") -> str:
    """Convert raw app ids into cleaner dashboard-facing names."""
    raw = (app_name or "").strip()
    title = (window_title or "").strip().casefold()
    normalized = raw.casefold()

    if normalized in {"python3", "python"} and "trackora" in title:
        return "Trackora"

    mapped = _APP_NAME_MAP.get(normalized)
    if mapped:
        return mapped

    if not raw:
        return "Unknown"

    return raw.replace("-", " ").replace("_", " ").title()
