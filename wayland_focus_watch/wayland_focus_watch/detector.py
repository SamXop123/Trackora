"""
Compose ordered backends until one returns a focused (app, title) pair.

Ordering rationale:
1. GNOME Shell extension (Window Calls) reads Mutter's focus directly when the
   user has installed the extension — best fidelity for window titles.
2. AT-SPI2 works on a stock GNOME session without extensions by querying the
   accessibility registry over D-Bus (not X11).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from wayland_focus_watch.backends import DEFAULT_BACKENDS


class FocusDetector:
    """Try each backend in order; first non-None result wins."""

    def __init__(self, backends: Sequence[object] | None = None) -> None:
        # Each backend exposes ``try_get() -> tuple[str, str] | None``.
        self._backends: Iterable[object] = backends or DEFAULT_BACKENDS

    def snapshot(self) -> tuple[str, str]:
        """
        Return (application_name, window_title).

        When nothing matches, ("Unknown", "") keeps the printer stable.
        """
        for backend in self._backends:
            getter = getattr(backend, "try_get", None)
            if getter is None:
                continue
            try:
                result = getter()
            except Exception:
                # A broken extension or transient AT-SPI glitch should not stop
                # the loop; the next backend may still succeed.
                continue
            if result is not None:
                app, title = result
                return str(app), str(title)
        return "Unknown", ""
