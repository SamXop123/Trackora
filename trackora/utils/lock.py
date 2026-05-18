"""Advisory file locks for single-instance Trackora processes."""

from __future__ import annotations

import fcntl
from pathlib import Path


class TrackoraInstanceLock:
    """Hold an exclusive advisory lock on a filesystem path."""

    def __init__(self, lock_path: Path) -> None:
        self._lock_path = lock_path.expanduser()
        self._lock_file = None

    def acquire(self) -> bool:
        """Acquire the lock without blocking."""
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = self._lock_path.open("a+", encoding="utf-8")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            return False

        handle.seek(0)
        handle.truncate()
        handle.write(str(self._lock_path))
        handle.flush()
        self._lock_file = handle
        return True

    def release(self) -> None:
        """Release the lock if held."""
        if self._lock_file is None:
            return

        fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_UN)
        self._lock_file.close()
        self._lock_file = None

    def __enter__(self) -> "TrackoraInstanceLock":
        if not self.acquire():
            raise RuntimeError("Trackora tracker is already running")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.release()
