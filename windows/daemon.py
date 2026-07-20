from __future__ import annotations

import sys
import subprocess
import time
from pathlib import Path

from trackora.utils.lock import TrackoraInstanceLock
from trackora.utils.paths import default_lock_path, default_log_path


def is_service_active_win() -> bool:
    """Check if the Trackora daemon is running by checking the advisory lock file."""
    lock = TrackoraInstanceLock(default_lock_path())
    if lock.acquire():
        # Successfully acquired the lock, which means the daemon is NOT running.
        lock.release()
        return False
    # Could not acquire the lock, indicating another instance (the daemon) has it.
    return True


def try_start_service_win() -> bool:
    """Spawn the Trackora tracking daemon as a background process on Windows."""
    if is_service_active_win():
        return True

    log_path = default_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    if getattr(sys, "frozen", False):
        daemon_exe = Path(sys.executable).parent / "trackora.exe"
        cmd = [str(daemon_exe)]
    else:
        cmd = [sys.executable, "-m", "trackora"]

    try:
        log_file = log_path.open("a", encoding="utf-8")
        # Start the Python module detached with no command window popping up
        subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=log_file,
            creationflags=subprocess.CREATE_NO_WINDOW,
            close_fds=True,
        )
        # Close the parent handle immediately as Popen duplicates it for the child
        log_file.close()

        # Wait briefly for startup and locking validation
        for _ in range(10):
            time.sleep(0.2)
            if is_service_active_win():
                return True
    except Exception:
        pass
        
    return False
