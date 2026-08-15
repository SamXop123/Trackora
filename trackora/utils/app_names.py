"""Display-name normalization for tracked application identifiers."""

from __future__ import annotations


_APP_NAME_MAP: dict[str, str] = {
    # Development
    "code": "VS Code",
    "code-oss": "VS Code",
    "vscode": "VS Code",
    "visual studio code": "VS Code",
    "devenv": "Visual Studio",
    "idea64": "IntelliJ IDEA",
    "idea": "IntelliJ IDEA",
    "pycharm64": "PyCharm",
    "pycharm": "PyCharm",
    "webstorm64": "WebStorm",
    "webstorm": "WebStorm",
    "clion64": "CLion",
    "sublime_text": "Sublime Text",
    "atom": "Atom",
    "antigravity": "Antigravity",

    # Terminals & Shells
    "windowsterminal": "Windows Terminal",
    "cmd": "Command Prompt",
    "powershell": "PowerShell",
    "pwsh": "PowerShell",
    "wt": "Windows Terminal",
    "kitty": "Kitty",
    "alacritty": "Alacritty",
    "org.gnome.console": "Console",
    "gnome-console": "Console",
    "gnome-terminal": "Terminal",

    # Browsers
    "google-chrome": "Chrome",
    "chrome": "Chrome",
    "msedge": "Microsoft Edge",
    "edge": "Microsoft Edge",
    "chromium": "Chromium",
    "brave-browser": "Brave",
    "brave": "Brave",
    "firefox": "Firefox",
    "opera": "Opera",
    "vivaldi": "Vivaldi",
    "zen": "Zen Browser",
    "arc": "Arc",

    # Communication & Social
    "discord": "Discord",
    "slack": "Slack",
    "telegram-desktop": "Telegram",
    "telegram": "Telegram",
    "whatsapp.root": "WhatsApp",
    "whatsapp": "WhatsApp",
    "teams": "Microsoft Teams",
    "ms-teams": "Microsoft Teams",
    "zoom": "Zoom",
    "signal": "Signal",

    # Media & Entertainment
    "spotify": "Spotify",
    "vlc": "VLC",
    "steam": "Steam",
    "steamwebhelper": "Steam",

    # System & Utilities
    "explorer": "File Explorer",
    "file explorer": "File Explorer",
    "notepad": "Notepad",
    "notepads": "Notepad",
    "taskmgr": "Task Manager",
    "org.gnome.nautilus": "Files",
    "nautilus": "Files",
    "org.gnome.settings": "Settings",
    "gnome-control-center": "Settings",
    "trackora": "Trackora",
}


def normalize_app_name(app_name: str, window_title: str = "") -> str:
    """Convert raw app ids into cleaner dashboard-facing names."""
    raw = (app_name or "").strip()
    title = (window_title or "").strip().casefold()
    
    # Strip .exe if present (Windows process names)
    if raw.lower().endswith(".exe"):
        raw = raw[:-4].strip()
        
    normalized = raw.casefold()

    if normalized in {"python3", "python", "pythonw"} and ("trackora" in title or "excluded application" in title or "service status" in title or "select date" in title):
        return "Trackora"

    mapped = _APP_NAME_MAP.get(normalized)
    if mapped:
        return mapped

    # Check without dots / special chars (e.g. "whatsapp.root" -> "whatsapp")
    base_no_ext = normalized.split(".")[0]
    if base_no_ext in _APP_NAME_MAP:
        return _APP_NAME_MAP[base_no_ext]

    if not raw:
        return "Unknown"

    return raw.replace("-", " ").replace("_", " ").title()
