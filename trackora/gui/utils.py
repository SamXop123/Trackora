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
        if app_name.lower() in ("trackora", "trackora dashboard", "trackora-dashboard"):
            from trackora.utils.paths import get_asset_path
            logo_path = get_asset_path("trackora_logo.png")
            exe_path = str(logo_path) if logo_path.exists() else None
        else:
            exe_path = _find_win32_exe_path(app_name)
        if exe_path:
            try:
                if exe_path.lower().endswith((".png", ".jpg", ".jpeg")):
                    icon = QIcon(exe_path)
                    if not icon.isNull():
                        pixmap = icon.pixmap(size, size)
                else:
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
            # Fuzzy match keys: case-insensitive + check space replacement variants
            target_lower = app_name.lower()
            variants = {target_lower, target_lower.replace(" ", "-"), target_lower.replace(" ", "_")}
            for key, val in data.items():
                if key.lower() in variants:
                    if os.path.exists(val):
                        # Special check for UWP app icons!
                        if "WindowsApps" in val:
                            uwp_icon = _find_uwp_png_icon(val)
                            if uwp_icon:
                                return uwp_icon
                        return val
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

    # 4. Running processes scan (fuzzy matching)
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


def _find_uwp_png_icon(exe_path: str) -> str | None:
    """Scan the UWP package directory for a high-resolution logo PNG."""
    try:
        app_dir = os.path.dirname(exe_path)
        patterns = [
            "StoreLogo.scale-200.png",
            "StoreLogo.png",
            "medtile*.png",
            "TitleIcon32.scale-200.png",
            "logo.scale-200.png",
            "logo.png",
        ]
        for root, dirs, files in os.walk(app_dir):
            depth = root[len(app_dir):].count(os.sep)
            if depth > 2:
                continue
            for file in files:
                file_lower = file.lower()
                for p in patterns:
                    import fnmatch
                    if fnmatch.fnmatch(file_lower, p.lower()):
                        full_path = os.path.join(root, file)
                        if os.path.exists(full_path):
                            return full_path
    except Exception:
        pass
    return None
