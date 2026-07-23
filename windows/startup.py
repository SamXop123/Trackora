from __future__ import annotations

import sys
import winreg


def set_windows_startup(enabled: bool) -> bool:
    """Register or unregister Trackora in the Windows user login Run key."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    key_name = "Trackora"

    if getattr(sys, "frozen", False):
        # Package executable path for the dashboard (living in the same folder)
        from pathlib import Path
        dashboard_exe = Path(sys.executable).parent / "trackora-dashboard.exe"
        cmd = f'"{dashboard_exe}" --minimized'
    else:
        # Development script launch command
        cmd = f'"{sys.executable}" -m trackora.gui --minimized'

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, cmd)
        else:
            for k in (key_name, "TrackoraDaemon"):
                try:
                    winreg.DeleteValue(key, k)
                except FileNotFoundError:
                    pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def is_windows_startup_enabled() -> bool:
    """Check if the Trackora autostart registry entry exists."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    
    for key_name in ("Trackora", "TrackoraDaemon"):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, key_name)
            winreg.CloseKey(key)
            if value:
                return True
        except FileNotFoundError:
            continue
        except Exception:
            continue
    return False
