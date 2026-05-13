"""
AT-SPI2 focus detection (accessibility tree over D-Bus).

On Wayland there is no portable "get active window" syscall for clients.
GNOME publishes application and window metadata to the AT-SPI registry on the
session accessibility bus. Walking the tree for a focused accessible, then
resolving the owning ``Atspi.Role.APPLICATION`` and a top-level ``FRAME`` /
``WINDOW`` / ``DIALOG`` name, matches what screen readers use and avoids X11
``_NET_ACTIVE_WINDOW`` entirely.

Note: This requires a working AT-SPI session (``at-spi-bus-launcher`` is part of
a normal GNOME login). If the registry is unreachable, this backend returns
None.
"""

from __future__ import annotations

import gi

gi.require_version("Atspi", "2.0")
from gi.repository import Atspi

# Roles that commonly carry the visible window title in GNOME/GTK/Qt stacks.
_TITLE_ROLES = frozenset(
    {
        Atspi.Role.FRAME,
        Atspi.Role.WINDOW,
        Atspi.Role.DIALOG,
    }
)


class AtspiFocusBackend:
    """Resolve focused window via the AT-SPI2 registry."""

    def __init__(self) -> None:
        self._initialized = False

    def _ensure_init(self) -> None:
        if self._initialized:
            return
        # ``init`` can report failure on some setups, but the registry may still
        # answer; we only need a one-time best-effort initialization.
        Atspi.init()
        self._initialized = True

    def try_get(self) -> tuple[str, str] | None:
        self._ensure_init()

        try:
            desktop = Atspi.get_desktop(0)
        except Exception:
            return None

        focused = self._find_focused_under(desktop, max_depth=48)
        if focused is None:
            return None

        app = self._application_name(focused)
        title = self._window_title(focused)
        if not app and not title:
            return None
        return app or "Unknown", title

    def _find_focused_under(
        self, root: Atspi.Accessible, max_depth: int, depth: int = 0
    ) -> Atspi.Accessible | None:
        """
        Depth-first search for an accessible with STATE_FOCUSED.

        We bound depth so a pathological tree cannot stall the poller; GNOME
        apps are typically well under this limit for the path to the focus.
        """
        if depth > max_depth:
            return None

        try:
            if self._has_focus(root):
                return root
        except Exception:
            # Some nodes reject state queries; skip them.
            pass

        try:
            n = root.get_child_count()
        except Exception:
            return None

        for i in range(n):
            try:
                child = root.get_child_at_index(i)
            except Exception:
                continue
            found = self._find_focused_under(child, max_depth, depth + 1)
            if found is not None:
                return found
        return None

    def _has_focus(self, acc: Atspi.Accessible) -> bool:
        states = acc.get_state_set()
        return states.contains(Atspi.StateType.FOCUSED)

    def _application_name(self, start: Atspi.Accessible) -> str:
        try:
            app = start.get_application()
            name = (app.get_name() or "").strip()
            if name:
                return name
        except Exception:
            pass

        cur: Atspi.Accessible | None = start
        while cur is not None:
            try:
                if cur.get_role() == Atspi.Role.APPLICATION:
                    name = (cur.get_name() or "").strip()
                    return name or "Unknown"
            except Exception:
                break
            try:
                cur = cur.get_parent()
            except Exception:
                break
        return "Unknown"

    def _window_title(self, start: Atspi.Accessible) -> str:
        """Walk ancestors for the first non-empty title-like accessible name."""
        cur: Atspi.Accessible | None = start
        while cur is not None:
            try:
                role = cur.get_role()
                if role in _TITLE_ROLES:
                    name = (cur.get_name() or "").strip()
                    if name:
                        return name
            except Exception:
                pass
            try:
                cur = cur.get_parent()
            except Exception:
                break
        return ""
