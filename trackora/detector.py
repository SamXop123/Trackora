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

from trackora.backends import DEFAULT_BACKENDS


def _is_shell_surface(app: str, title: str) -> bool:
    """
    Ignore compositor-owned shell surfaces such as GNOME's main stage.

    Returning these as the "active app" is misleading for activity tracking and
    also prevents later backends from supplying a real focused window.
    """
    normalized_app = app.strip().casefold()
    normalized_title = title.strip().casefold()

    if normalized_app in {"gnome-shell", "gnome shell"}:
        return True
    return normalized_title == "main stage"


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
                if _is_shell_surface(str(app), str(title)):
                    continue
                return str(app), str(title)
        return "Unknown", ""
