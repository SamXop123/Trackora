from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import sys

from trackora.window_state import WindowStateProvider, WindowStateReadResult
from trackora.models.window_state import WindowState
from trackora.utils.time import now_utc, to_storage_timestamp

# Load user32 and kernel32 once
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Configure win32 API types explicitly to prevent truncation of 64-bit handles
user32.GetForegroundWindow.argtypes = []
user32.GetForegroundWindow.restype = wintypes.HWND

user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int

user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int

user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetClassNameW.restype = ctypes.c_int

user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user32.GetWindowThreadProcessId.restype = wintypes.DWORD

kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE

kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD)
]
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]


user32.GetLastInputInfo.argtypes = [ctypes.POINTER(LASTINPUTINFO)]
user32.GetLastInputInfo.restype = wintypes.BOOL

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL

user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL

user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsIconic.restype = wintypes.BOOL

user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long


def _get_win32_idle_seconds() -> float:
    """Return seconds since last physical keyboard/mouse input on Windows."""
    try:
        lii = LASTINPUTINFO()
        lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if user32.GetLastInputInfo(ctypes.byref(lii)):
            millis = (kernel32.GetTickCount() & 0xFFFFFFFF) - (lii.dwTime & 0xFFFFFFFF)
            if millis < 0:
                millis += 0x100000000
            return millis / 1000.0
    except Exception:
        pass
    return 0.0


def _has_non_minimized_app_windows() -> bool:
    """Return True if there is at least one visible, non-minimized top-level application window on screen."""
    found = [False]

    def enum_proc(hwnd: wintypes.HWND, lparam: wintypes.LPARAM) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        if user32.IsIconic(hwnd):
            return True

        buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, buf, 256)
        cls = buf.value

        ignored_classes = (
            "Progman", "WorkerW", "SHELLDLL_DefView", "SysListView32",
            "Shell_TrayWnd", "Shell_SecondaryTrayWnd", "Windows.UI.Core.CoreWindow",
            "DV2ControlHost", "MultitaskingViewFrame", "XamlExplorerHost",
            "LockScreenHost"
        )
        if cls in ignored_classes:
            return True

        ex_style = user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE: -20
        # WS_EX_TOOLWINDOW: 0x00000080, WS_EX_APPWINDOW: 0x00040000
        if (ex_style & 0x00000080) and not (ex_style & 0x00040000):
            return True

        found[0] = True
        return False

    cb = WNDENUMPROC(enum_proc)
    user32.EnumWindows(cb, 0)
    return found[0]


class WindowsNativeWindowStateProvider(WindowStateProvider):
    """Native active window provider for Windows using ctypes APIs."""

    def __init__(self, idle_threshold_sec: float = 300.0) -> None:
        super().__init__()
        self._saved_paths: dict[str, str] = {}
        self.idle_threshold_sec = idle_threshold_sec

    def get_window_state(self) -> WindowStateReadResult:
        if sys.platform != "win32":
            return WindowStateReadResult(state=None, error="Windows tracker can only run on Windows")

        try:
            # 0. Check physical user input idle threshold (AFK detection)
            idle_sec = _get_win32_idle_seconds()
            if idle_sec >= self.idle_threshold_sec:
                return WindowStateReadResult(state=None, error=f"User idle / AFK for {idle_sec:.1f}s")

            # 1. Fetch active window handle
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                # No window focused (screen locked, display off, lid closed, or system asleep)
                return WindowStateReadResult(state=None, error="No active window focused")

            # 2. Query window class name to detect desktop shell focus
            class_name = ""
            class_buf = ctypes.create_unicode_buffer(256)
            if user32.GetClassNameW(hwnd, class_buf, 256) > 0:
                class_name = class_buf.value

            desktop_classes = ("Progman", "WorkerW", "SHELLDLL_DefView", "SysListView32")
            transient_shell_classes = (
                "Shell_TrayWnd",
                "Shell_SecondaryTrayWnd",
                "Windows.UI.Core.CoreWindow",
                "DV2ControlHost",
                "MultitaskingViewFrame",
                "XamlExplorerHost"
            )

            if class_name in desktop_classes:
                # Desktop should ONLY be counted when every application is minimized
                # and directly the desktop is visible!
                if _has_non_minimized_app_windows():
                    return WindowStateReadResult(state=None, error=f"Transient desktop click while apps open ({class_name})")
                state = WindowState(
                    app="Desktop",
                    title="Desktop",
                    timestamp=to_storage_timestamp(now_utc())
                )
                return WindowStateReadResult(state=state, error=None)
            elif class_name in transient_shell_classes:
                return WindowStateReadResult(state=None, error=f"Transient taskbar/shell focus: {class_name}")

            # 3. Query window title
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
            else:
                title = ""

            # 4. Query associated Process ID
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            # 5. Open process to retrieve its executable filename
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h_process = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            app = "Unknown"

            if h_process:
                try:
                    buf_size = ctypes.c_ulong(1024)
                    buf = ctypes.create_unicode_buffer(buf_size.value)
                    if kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(buf_size)):
                        exe_path = buf.value
                        exe_name = os.path.basename(exe_path)
                        # Strip extension, e.g. "chrome.exe" -> "chrome"
                        app = os.path.splitext(exe_name)[0]
                        if app.lower() in ("lockapp", "logonui", "scrnsave"):
                            return WindowStateReadResult(state=None, error="System locked / sleep screen")
                        if app.lower() == "explorer":
                            if class_name in desktop_classes:
                                if _has_non_minimized_app_windows():
                                    return WindowStateReadResult(state=None, error=f"Transient explorer desktop click while apps open ({class_name})")
                                app = "Desktop"
                                title = "Desktop"
                            elif class_name in ("CabinetWClass", "ExploreWClass"):
                                app = "File Explorer"
                                if not title:
                                    title = "File Explorer"
                            else:
                                return WindowStateReadResult(state=None, error=f"Transient shell focus: {class_name}")
                        self._save_exe_path(app, exe_path)
                finally:
                    kernel32.CloseHandle(h_process)

            if not app:
                app = "Unknown"

            state = WindowState(
                app=app,
                title=title,
                timestamp=to_storage_timestamp(now_utc())
            )
            return WindowStateReadResult(state=state, error=None)

        except Exception as exc:
            return WindowStateReadResult(state=None, error=f"Win32 API error: {exc}")

    def _save_exe_path(self, app_name: str, exe_path: str) -> None:
        """Save the resolved executable path mapping to a JSON cache for the GUI icon provider."""
        if self._saved_paths.get(app_name) == exe_path:
            return

        self._saved_paths[app_name] = exe_path
        try:
            from trackora.utils.paths import trackora_data_dir
            import json
            cache_file = trackora_data_dir() / "exe_paths.json"

            cache = {}
            if cache_file.exists():
                try:
                    cache = json.loads(cache_file.read_text(encoding="utf-8"))
                except Exception:
                    pass

            if cache.get(app_name) != exe_path:
                cache[app_name] = exe_path
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(json.dumps(cache, indent=4), encoding="utf-8")

            self._saved_paths.update(cache)
        except Exception:
            pass
