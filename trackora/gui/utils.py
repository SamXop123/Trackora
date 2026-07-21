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
    """Find Windows executable path for app_name via cache, registry, Start Menu shortcuts, or processes."""
    if not app_name:
        return None

    # 1. Check daemon's JSON path cache
    try:
        from trackora.utils.paths import trackora_data_dir
        import json
        cache_file = trackora_data_dir() / "exe_paths.json"
        if cache_file.exists():
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if app_name in data:
                path = data[app_name]
                if os.path.exists(path):
                    return path
    except Exception:
        pass

    # 2. Hardcoded system apps fallbacks
    sys_fallbacks = {
        "explorer": os.path.join(os.environ.get("windir", "C:\\Windows"), "explorer.exe"),
        "taskmgr": os.path.join(os.environ.get("windir", "C:\\Windows\\System32"), "taskmgr.exe"),
        "cmd": os.path.join(os.environ.get("windir", "C:\\Windows\\System32"), "cmd.exe"),
        "powershell": os.path.join(os.environ.get("windir", "C:\\Windows\\System32\\WindowsPowerShell\\v1.0"), "powershell.exe"),
    }
    app_lower = app_name.lower()
    if app_lower in sys_fallbacks:
        path = sys_fallbacks[app_lower]
        if os.path.exists(path):
            return path

    # 3. Registry App Paths
    try:
        import winreg
        for name in (app_name, f"{app_name}.exe"):
            for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                key_path = f"Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{name}"
                try:
                    with winreg.OpenKey(root, key_path) as key:
                        val, _ = winreg.QueryValueEx(key, "")
                        if val and os.path.exists(val):
                            return val
                except OSError:
                    continue
    except Exception:
        pass

    # 4. Start Menu shortcuts scan
    try:
        path = _find_app_via_shortcuts(app_name)
        if path:
            return path
    except Exception:
        pass

    # 5. Running processes scan (fuzzy matching)
    try:
        import psutil
        target = app_name.lower()
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                pname = proc.info['name']
                if pname:
                    pname_no_ext = pname.lower().split('.')[0]
                    if target in pname_no_ext or pname_no_ext in target or pname.lower() == target:
                        exe = proc.info['exe']
                        if exe and os.path.exists(exe):
                            return exe
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass

    return None


def _find_app_via_shortcuts(app_name: str) -> str | None:
    """Scan standard Windows Start Menu directories for .lnk files matching app_name and resolve target."""
    user_appdata = os.environ.get("APPDATA")
    program_data = os.environ.get("PROGRAMDATA")

    search_dirs = []
    if user_appdata:
        search_dirs.append(os.path.join(user_appdata, "Microsoft", "Windows", "Start Menu", "Programs"))
    if program_data:
        search_dirs.append(os.path.join(program_data, "Microsoft", "Windows", "Start Menu", "Programs"))

    target_name = app_name.lower()

    for base_dir in search_dirs:
        if not os.path.exists(base_dir):
            continue

        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".lnk"):
                    name_no_ext = os.path.splitext(file)[0].lower()
                    if target_name in name_no_ext or name_no_ext in target_name:
                        full_path = os.path.join(root, file)
                        try:
                            import win32com.client
                            shell = win32com.client.Dispatch("WScript.Shell")
                            shortcut = shell.CreateShortcut(full_path)
                            target = shortcut.TargetPath
                            if target and os.path.exists(target) and target.endswith(".exe"):
                                return target
                        except Exception:
                            pass
    return None
