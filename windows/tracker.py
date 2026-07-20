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


class WindowsNativeWindowStateProvider(WindowStateProvider):
    """Native active window provider for Windows using ctypes APIs."""

    def get_window_state(self) -> WindowStateReadResult:
        if sys.platform != "win32":
            return WindowStateReadResult(state=None, error="Windows tracker can only run on Windows")

        try:
            # 1. Fetch active window handle
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return WindowStateReadResult(state=None, error="No active window focused")

            # 2. Query window title
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value
            else:
                title = ""

            # 3. Query associated Process ID
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            # 4. Open process to retrieve its executable filename
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
