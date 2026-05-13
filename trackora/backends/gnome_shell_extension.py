"""
GNOME Shell extension D-Bus: Window Calls / compatible extensions.

The stock GNOME Shell session bus does not expose a stable public API for the
focused MetaWindow on Wayland (unlike legacy X11 _NET_ACTIVE_WINDOW). Many
users install the community "Window Calls" extension, which exports
``org.gnome.Shell.Extensions.Windows`` with a ``List`` method returning JSON
for each window, including ``focus`` and ``title``.

This backend is optional: if the extension is not enabled, ``try_get`` returns
None and the detector falls back to AT-SPI2.
"""

from __future__ import annotations

import json
from typing import Any

from gi.repository import Gio, GLib


SHELL_BUS_NAME = "org.gnome.Shell"
WINDOWS_OBJECT_PATH = "/org/gnome/Shell/Extensions/Windows"
WINDOWS_INTERFACE = "org.gnome.Shell.Extensions.Windows"


def _pretty_app_name(wm_class_instance: str | None, wm_class: str | None) -> str:
    """Derive a short display name from WM_CLASS fields."""
    if wm_class_instance and wm_class_instance.strip():
        # e.g. "code", "firefox" -> title-cased for display
        return wm_class_instance.strip().replace("-", " ").title()
    if wm_class and wm_class.strip():
        # WM_CLASS often uses NUL-separated instance and class names.
        first = wm_class.split("\0", 1)[0].strip()
        return first.replace("-", " ").title() if first else "Unknown"
    return "Unknown"


def _is_shell_internal_window(window: dict[str, Any]) -> bool:
    """
    Ignore GNOME Shell's own internal stage/overview surfaces.

    Some Window Calls setups report the compositor itself as focused with
    titles like "Main stage". Those are not real user app windows, so letting
    them through prevents the detector from falling back to more useful
    backends.
    """
    instance = str(window.get("wm_class_instance") or "").strip().casefold()
    wm_class = str(window.get("wm_class") or "").strip().casefold()
    title = str(window.get("title") or "").strip().casefold()

    if instance == "gnome-shell":
        return True
    if wm_class.startswith("gnome-shell"):
        return True
    return title == "main stage"


class GnomeShellWindowCallsBackend:
    """Query Window Calls-style ``List`` over the session D-Bus."""

    def try_get(self) -> tuple[str, str] | None:
        """
        If the extension is present, return (app_name, window_title).

        Returns None when the object path or method is unavailable, or when no
        window reports ``focus: true`` in the payload.
        """
        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            reply = bus.call_sync(
                SHELL_BUS_NAME,
                WINDOWS_OBJECT_PATH,
                WINDOWS_INTERFACE,
                "List",
                None,
                GLib.VariantType("(s)"),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except GLib.Error:
            # Typical cases: UnknownObject (extension off), UnknownMethod.
            return None

        payload = reply.unpack()[0]
        try:
            windows: list[dict[str, Any]] = json.loads(payload)
        except json.JSONDecodeError:
            return None

        focused = None
        for w in windows:
            if w.get("focus") is True and not _is_shell_internal_window(w):
                focused = w
                break
        if focused is None:
            return None

        title = str(focused.get("title") or "")
        app = _pretty_app_name(
            focused.get("wm_class_instance"),
            focused.get("wm_class"),
        )
        return app, title
