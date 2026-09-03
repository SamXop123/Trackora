"""Display-name normalization for tracked application identifiers."""

from __future__ import annotations


import glob
import os
import sys

_APP_NAME_MAP: dict[str, str] = {
    # Development
    "code": "VS Code",
    "code-oss": "VS Code",
    "vscode": "VS Code",
    "visual studio code": "VS Code",
    "com.visualstudio.code": "VS Code",
    "com.visualstudio.code.oss": "VS Code",
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

    # Productivity & Notes
    "obsidian": "Obsidian",
    "md.obsidian": "Obsidian",
    "md.obsidian.obsidian": "Obsidian",

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
    "org.gnome.terminal": "Terminal",
    "org.gnome.ptyxis": "Terminal",

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
    "whatsappdesktop": "WhatsApp",
    "teams": "Microsoft Teams",
    "ms-teams": "Microsoft Teams",
    "zoom": "Zoom",
    "signal": "Signal",

    # Media & Entertainment
    "spotify": "Spotify",
    "vlc": "VLC",
    "steam": "Steam",
    "steamwebhelper": "Steam",
    "org.gnome.showtime": "Videos",
    "org.gnome.decibels": "Audio Player",

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
    "org.gnome.papers": "Document Viewer",
    "org.gnome.papers.desktop": "Document Viewer",
    "gnome.org.papers": "Document Viewer",
    "gnome-papers": "Document Viewer",
    "papers": "Document Viewer",
    "org.gnome.calculator": "Calculator",
    "org.gnome.calendar": "Calendar",
    "org.gnome.texteditor": "Text Editor",
    "org.gnome.loupe": "Image Viewer",
    "org.freedesktop.gnomeabrt": "Problem Reporting",
    "systemsettings": "Settings",
    "onenoteim": "OneNote",
    "onenote": "OneNote",
    "calculatorapp": "Calculator",
    "microsoft.photos": "Photos",
    "photosapp": "Photos",
    "trackora": "Trackora",
    "trackora-dashboard": "Trackora",
    "trackora dashboard": "Trackora",
}

_LINUX_DESKTOP_CACHE: dict[str, tuple[str, str]] | None = None


def _get_linux_desktop_index() -> dict[str, tuple[str, str]]:
    """Scan and cache Linux application .desktop files for Name= and Icon= metadata."""
    global _LINUX_DESKTOP_CACHE
    if _LINUX_DESKTOP_CACHE is not None:
        return _LINUX_DESKTOP_CACHE

    _LINUX_DESKTOP_CACHE = {}
    if sys.platform == "win32":
        return _LINUX_DESKTOP_CACHE

    desktop_dirs = [
        "/usr/share/applications",
        "/usr/local/share/applications",
        os.path.expanduser("~/.local/share/applications"),
        "/var/lib/flatpak/exports/share/applications",
        os.path.expanduser("~/.local/share/flatpak/exports/share/applications"),
        "/var/lib/snapd/desktop/applications",
    ]

    for d in desktop_dirs:
        if not os.path.exists(d):
            continue
        try:
            for path in glob.glob(os.path.join(d, "*.desktop")):
                app_id = os.path.basename(path)
                if app_id.lower().endswith(".desktop"):
                    app_id = app_id[:-8]
                app_id_lower = app_id.lower()

                name, icon = None, None
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    in_entry = False
                    for line in f:
                        line = line.strip()
                        if line == "[Desktop Entry]":
                            in_entry = True
                            continue
                        elif line.startswith("[") and line.endswith("]"):
                            in_entry = False
                        if in_entry:
                            if line.startswith("Name=") and not name:
                                name = line[5:].strip()
                            elif line.startswith("Icon=") and not icon:
                                icon = line[5:].strip()
                            if name and icon:
                                break
                if name:
                    _LINUX_DESKTOP_CACHE[app_id_lower] = (name, icon or "")
        except Exception:
            pass

    return _LINUX_DESKTOP_CACHE


def _find_linux_desktop_name(raw_app: str) -> str | None:
    """Find desktop app Name from Linux .desktop files by app ID or reverse-DNS prefix."""
    index = _get_linux_desktop_index()
    clean = raw_app.lower().strip()
    if clean.endswith(".desktop"):
        clean = clean[:-8]
    if not clean:
        return None

    if clean in index:
        return index[clean][0]

    for key, (name, _) in index.items():
        if key.startswith(clean + ".") or key.endswith("." + clean) or clean in key.split("."):
            return name

    return None


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

    if normalized == "applicationframehost":
        if "onenote" in title:
            return "OneNote"
        if "settings" in title:
            return "Settings"
        if "whatsapp" in title:
            return "WhatsApp"
        if "calculator" in title:
            return "Calculator"
        if "photos" in title:
            return "Photos"

    mapped = _APP_NAME_MAP.get(normalized)
    if mapped:
        return mapped

    # Check Linux desktop entry files
    desktop_name = _find_linux_desktop_name(raw)
    if desktop_name:
        return desktop_name

    # Check reverse-DNS segments (e.g. md.obsidian.obsidian -> obsidian -> Obsidian)
    parts = [p for p in normalized.split(".") if p]
    for p in reversed(parts):
        if p in _APP_NAME_MAP:
            return _APP_NAME_MAP[p]

    if not raw:
        return "Unknown"

    return raw.replace("-", " ").replace("_", " ").title()

