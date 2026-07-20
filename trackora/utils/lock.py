"""Advisory file locks for single-instance Trackora processes."""

from __future__ import annotations

import os
from pathlib import Path


class TrackoraAlreadyRunningError(RuntimeError):
    """Raised when another Trackora tracker instance already holds the lock."""


class TrackoraInstanceLock:
    """Hold an exclusive advisory lock on a filesystem path."""

    def __init__(self, lock_path: Path) -> None:
        self._lock_path = lock_path.expanduser()
        self._lock_file = None

    def acquire(self) -> bool:
        """Acquire the lock without blocking."""
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        
        import sys
        if sys.platform == "win32":
            import msvcrt
            try:
                handle = self._lock_path.open("a+", encoding="utf-8")
            except OSError:
                return False
            try:
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                handle.close()
                return False
        else:
            import fcntl
            try:
                handle = self._lock_path.open("a+", encoding="utf-8")
            except OSError:
                return False
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                handle.close()
                return False

        handle.seek(0)
        handle.truncate()
        handle.write(str(os.getpid()))
        handle.flush()
        self._lock_file = handle
        return True

    def release(self) -> None:
        """Release the lock if held."""
        if self._lock_file is None:
            return

        import sys
        if sys.platform == "win32":
            import msvcrt
            try:
                self._lock_file.seek(0)
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            import fcntl
            try:
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass

        self._lock_file.close()
        self._lock_file = None

    def __enter__(self) -> "TrackoraInstanceLock":
        if not self.acquire():
            raise TrackoraAlreadyRunningError(
                "Trackora tracker is already running. No second tracker instance was started."
            )
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()
