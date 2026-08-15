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

from typing import Callable
from collections import defaultdict
from PySide6.QtCore import QObject, QRunnable, QSize, QThreadPool, Signal

# In-memory cache for resolved icons to avoid heavy scans
_ICON_CACHE: dict[str, QPixmap] = {}
_MISSING_ICON_CACHE: set[str] = set()
_PENDING_ICON_CALLBACKS: dict[str, list[Callable[[QPixmap | None], None]]] = defaultdict(list)
_RESOLVING_ICONS: set[str] = set()


class _IconWorkerSignals(QObject):
    icon_loaded = Signal(str, int, object)  # app_name, size, QPixmap or None


_SIGNALS: _IconWorkerSignals | None = None


def _get_signals() -> _IconWorkerSignals:
    global _SIGNALS
    if _SIGNALS is None:
        _SIGNALS = _IconWorkerSignals()
        _SIGNALS.icon_loaded.connect(_on_icon_loaded_slot)
    return _SIGNALS


def _on_icon_loaded_slot(app_name: str, size: int, pixmap: QPixmap | None) -> None:
    cache_key = f"{app_name}_{size}"
    callbacks = _PENDING_ICON_CALLBACKS.pop(cache_key, [])
    for cb in callbacks:
        try:
            cb(pixmap)
        except Exception:
            pass


class _AsyncIconTask(QRunnable):
    def __init__(self, app_name: str, size: int):
        super().__init__()
        self.app_name = app_name
        self.size = size

    def run(self) -> None:
        try:
            pixmap = _resolve_app_icon_sync(self.app_name, self.size)
        except Exception:
            pixmap = None
        finally:
            _RESOLVING_ICONS.discard(f"{self.app_name}_{self.size}")
            try:
                _get_signals().icon_loaded.emit(self.app_name, self.size, pixmap)
            except Exception:
                pass


def _resolve_app_icon_sync(app_name: str, size: int) -> QPixmap | None:
    """Internal synchronous icon resolver."""
    cache_key = f"{app_name}_{size}"
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]
    if cache_key in _MISSING_ICON_CACHE:
        return None

    pixmap = None

    if app_name.lower() == "desktop":
        if sys.platform == "win32":
            try:
                from PySide6.QtWidgets import QFileIconProvider
                provider = QFileIconProvider()
                icon = provider.icon(QFileIconProvider.IconType.Desktop)
                if not icon.isNull():
                    pixmap = icon.pixmap(size, size)
            except Exception:
                pass
        else:
            candidates = ["user-desktop", "desktop", "preferences-desktop-wallpaper", "preferences-desktop"]
            for name in candidates:
                icon = QIcon.fromTheme(name)
                if not icon.isNull():
                    pixmap = icon.pixmap(QSize(size, size))
                    break
    elif sys.platform == "win32":
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

    if pixmap is not None:
        _ICON_CACHE[cache_key] = pixmap
    else:
        _MISSING_ICON_CACHE.add(cache_key)

    return pixmap


def get_app_icon(
    app_name: str,
    size: int = 24,
    on_loaded: Callable[[QPixmap | None], None] | None = None,
) -> QPixmap | None:
    """Retrieve application icon.
    
    If on_loaded is provided and icon is not yet cached, it resolves the icon
    asynchronously in the background without blocking the UI thread (0ms latency).
    """
    cache_key = f"{app_name}_{size}"
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]
    if cache_key in _MISSING_ICON_CACHE:
        return None

    if on_loaded is not None:
        _PENDING_ICON_CALLBACKS[cache_key].append(on_loaded)
        if cache_key not in _RESOLVING_ICONS:
            _RESOLVING_ICONS.add(cache_key)
            task = _AsyncIconTask(app_name, size)
            QThreadPool.globalInstance().start(task)
        return None

    # Fallback to synchronous resolution if no callback was passed
    return _resolve_app_icon_sync(app_name, size)


_WIN_APP_ALIASES: dict[str, list[str]] = {
    "vs code": ["code", "code.exe", "vscode", "visual studio code"],
    "vscode": ["code", "code.exe", "vs code"],
    "visual studio code": ["code", "code.exe", "vscode"],
    "code": ["code", "code.exe", "vscode", "vs code"],
    "chrome": ["chrome", "chrome.exe", "google chrome"],
    "firefox": ["firefox", "firefox.exe"],
    "brave": ["brave", "brave.exe", "brave-browser"],
    "spotify": ["spotify", "spotify.exe"],
    "discord": ["discord", "discord.exe"],
    "slack": ["slack", "slack.exe"],
    "telegram": ["telegram", "telegram.exe"],
}

_START_MENU_SHORTCUT_INDEX: dict[str, str] | None = None
_EXE_SEARCH_CACHE: dict[str, str | None] = {}
_EXE_PATHS_JSON_CACHE: dict[str, str] = {}
_EXE_PATHS_JSON_MTIME: float = -1.0


def _get_start_menu_shortcuts() -> dict[str, str]:
    global _START_MENU_SHORTCUT_INDEX
    if _START_MENU_SHORTCUT_INDEX is not None:
        return _START_MENU_SHORTCUT_INDEX

    _START_MENU_SHORTCUT_INDEX = {}
    start_menu_dirs = [
        os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
        os.path.join(os.environ.get("ALLUSERSPROFILE", ""), "Microsoft", "Windows", "Start Menu", "Programs"),
    ]
    for sm_dir in start_menu_dirs:
        if not os.path.exists(sm_dir):
            continue
        try:
            for root_dir, _, files in os.walk(sm_dir):
                for f in files:
                    if f.lower().endswith(".lnk"):
                        fname_lower = os.path.splitext(f.lower())[0]
                        if fname_lower not in _START_MENU_SHORTCUT_INDEX:
                            _START_MENU_SHORTCUT_INDEX[fname_lower] = os.path.join(root_dir, f)
        except Exception:
            pass
    return _START_MENU_SHORTCUT_INDEX


def _find_win32_exe_path(app_name: str) -> str | None:
    """Find Windows executable path for app_name via aliases, known paths, cache, registry, or Start Menu shortcuts."""
    if not app_name:
        return None

    app_lower = app_name.lower().strip()
    if app_lower in _EXE_SEARCH_CACHE:
        return _EXE_SEARCH_CACHE[app_lower]

    # 0. Check direct known installation paths for common desktop apps
    known_paths = {
        "vs code": [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Microsoft VS Code", "Code.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft VS Code", "Code.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft VS Code", "Code.exe"),
        ],
        "vscode": [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Microsoft VS Code", "Code.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft VS Code", "Code.exe"),
        ],
        "visual studio code": [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Microsoft VS Code", "Code.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft VS Code", "Code.exe"),
        ],
        "chrome": [
            os.path.join(os.environ.get("ProgramFiles", ""), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Google", "Chrome", "Application", "chrome.exe"),
        ],
        "edge": [
            os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Microsoft", "Edge", "Application", "msedge.exe"),
        ],
    }

    if app_lower in known_paths:
        for p in known_paths[app_lower]:
            if p and os.path.exists(p):
                _EXE_SEARCH_CACHE[app_lower] = p
                return p

    # Build search variants including aliases
    search_names = {app_lower, app_lower.replace(" ", "-"), app_lower.replace(" ", "_")}
    if app_lower in _WIN_APP_ALIASES:
        search_names.update(_WIN_APP_ALIASES[app_lower])

    # 1. Check daemon's JSON path cache (memory cached)
    try:
        from trackora.utils.paths import trackora_data_dir
        import json
        global _EXE_PATHS_JSON_MTIME, _EXE_PATHS_JSON_CACHE
        cache_file = trackora_data_dir() / "exe_paths.json"
        if cache_file.exists():
            mtime = cache_file.stat().st_mtime
            if mtime != _EXE_PATHS_JSON_MTIME:
                _EXE_PATHS_JSON_CACHE = json.loads(cache_file.read_text(encoding="utf-8"))
                _EXE_PATHS_JSON_MTIME = mtime
            for key, val in _EXE_PATHS_JSON_CACHE.items():
                if key.lower() in search_names:
                    if val and os.path.exists(val):
                        if "WindowsApps" in val:
                            uwp_icon = _find_uwp_png_icon(val)
                            if uwp_icon:
                                _EXE_SEARCH_CACHE[app_lower] = uwp_icon
                                return uwp_icon
                        _EXE_SEARCH_CACHE[app_lower] = val
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
    if app_lower in sys_fallbacks:
        path = sys_fallbacks[app_lower]
        if os.path.exists(path):
            _EXE_SEARCH_CACHE[app_lower] = path
            return path

    # 3. Registry App Paths
    try:
        import winreg
        for sname in search_names:
            for name in (sname, f"{sname}.exe"):
                for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                    key_path = f"Software\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{name}"
                    try:
                        with winreg.OpenKey(root, key_path) as key:
                            val, _ = winreg.QueryValueEx(key, "")
                            if val and os.path.exists(val):
                                _EXE_SEARCH_CACHE[app_lower] = val
                                return val
                    except OSError:
                        continue
    except Exception:
        pass

    # 4. Start Menu shortcuts scan using single-pass index
    try:
        sm_shortcuts = _get_start_menu_shortcuts()
        for sname in search_names:
            if sname in sm_shortcuts:
                _EXE_SEARCH_CACHE[app_lower] = sm_shortcuts[sname]
                return sm_shortcuts[sname]
        for key, path in sm_shortcuts.items():
            if any(sname in key for sname in search_names if len(sname) >= 3):
                _EXE_SEARCH_CACHE[app_lower] = path
                return path
    except Exception:
        pass

    _EXE_SEARCH_CACHE[app_lower] = None
    return None


def _find_uwp_png_icon(exe_path: str) -> str | None:
    """Scan the UWP package directory for a high-resolution logo PNG."""
    try:
        app_dir = os.path.dirname(exe_path)
        patterns = (
            "StoreLogo.scale-200.png",
            "StoreLogo.png",
            "TitleIcon32.scale-200.png",
            "logo.scale-200.png",
            "logo.png",
        )
        for pat in patterns:
            candidate = os.path.join(app_dir, pat)
            if os.path.exists(candidate):
                return candidate
            candidate_assets = os.path.join(app_dir, "Assets", pat)
            if os.path.exists(candidate_assets):
                return candidate_assets
    except Exception:
        pass
    return None
