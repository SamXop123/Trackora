from __future__ import annotations

import sys
import winreg


def set_windows_startup(enabled: bool) -> bool:
    """Register or unregister the Trackora daemon in the Windows user login Run key."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    key_name = "TrackoraDaemon"

    if getattr(sys, "frozen", False):
        # Package executable path
        cmd = f'"{sys.executable}"'
    else:
        # Development script launch command
        cmd = f'"{sys.executable}" -m trackora'

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, key_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def is_windows_startup_enabled() -> bool:
    """Check if the Trackora daemon autostart registry entry exists."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    key_name = "TrackoraDaemon"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, key_name)
        winreg.CloseKey(key)
        return bool(value)
    except FileNotFoundError:
        return False
    except Exception:
        return False
