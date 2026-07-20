"""Shared GUI utility functions."""

from __future__ import annotations

import os
import sys
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize

# Linux/GNOME icon theme candidate list
_ICON_THEME_MAP: dict[str, list[str]] = {
    "VS Code": ["code", "visual-studio-code", "com.visualstudio.code"],
    "Chrome": ["google-chrome", "chromium"],
    "Chromium": ["chromium"],
    "Brave": ["brave-browser"],
    "Firefox": ["firefox"],
    "Spotify": ["spotify"],
    "Discord": ["discord"],
    "Slack": ["slack"],
    "Telegram": ["telegram-desktop", "telegram"],
    "Files": ["org.gnome.Nautilus", "system-file-manager"],
    "Console": ["org.gnome.Console", "utilities-terminal"],
    "Settings": ["org.gnome.Settings", "preferences-system"],
    "Kitty": ["kitty"],
    "Terminal": ["org.gnome.Console", "utilities-terminal", "gnome-terminal"],
    "GitHub Desktop": ["github-desktop"],
    "Cursor": ["co.anysphere.cursor", "cursor"],
}
_FALLBACK_ICON = "application-x-executable"

# In-memory cache for resolved icons to avoid heavy scans
_ICON_CACHE: dict[str, QPixmap] = {}

def get_app_icon(app_name: str, size: int = 24) -> QPixmap | None:
    """Retrieve application icon in a platform-aware way (icon theme on Linux, shell executable icon on Windows)."""
    cache_key = f"{app_name}_{size}"
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    pixmap = None

    if sys.platform == "win32":
        # Windows native executable icon extraction
        exe_path = _find_win32_exe_path(app_name)
        if exe_path:
            try:
                from PySide6.QtWidgets import QFileIconProvider
                from PySide6.QtCore import QFileInfo
                provider = QFileIconProvider()
                icon = provider.icon(QFileInfo(exe_path))
                if not icon.isNull():
                    pixmap = icon.pixmap(size, size)
            except Exception:
                pass
    else:
        # Linux standard XDG desktop icon theme lookup
        candidates = _ICON_THEME_MAP.get(app_name, [app_name.lower().replace(" ", "-")])
        for name in candidates:
            icon = QIcon.fromTheme(name)
            if not icon.isNull():
                pixmap = icon.pixmap(QSize(size, size))
                break

    # Final fallback if nothing found
    if pixmap is None:
        try:
            if sys.platform == "win32":
                from PySide6.QtWidgets import QFileIconProvider
                provider = QFileIconProvider()
                icon = provider.icon(QFileIconProvider.IconType.File)
            else:
                icon = QIcon.fromTheme(_FALLBACK_ICON)
            
            if not icon.isNull():
                pixmap = icon.pixmap(QSize(size, size))
        except Exception:
            pass

    if pixmap is not None:
        _ICON_CACHE[cache_key] = pixmap

    return pixmap


def _find_win32_exe_path(app_name: str) -> str | None:
    """Find Windows executable path for app_name via registry App Paths or running process list."""
    if not app_name:
        return None

    # 1. Try Windows Registry App Paths
    try:
        import winreg
        for name in (app_name, f"{app_name}.exe"):
            for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                key_path = f"Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{name}"
                try:
                    with winreg.OpenKey(root, key_path) as key:
                        val, _ = winreg.QueryValueEx(key, "")
                        if val:
                            return val
                except OSError:
                    continue
    except Exception:
        pass

    # 2. Try looking up current running processes
    try:
        import psutil
        target = app_name.lower()
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                pname = proc.info['name']
                if pname:
                    pname_no_ext = pname.lower().split('.')[0]
                    if pname_no_ext == target or pname.lower() == target:
                        exe = proc.info['exe']
                        if exe:
                            return exe
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass

    return None
