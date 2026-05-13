"""Detection backends ordered from most specific to most general."""

from wayland_focus_watch.backends.atspi_backend import AtspiFocusBackend
from wayland_focus_watch.backends.gnome_shell_extension import (
    GnomeShellWindowCallsBackend,
)

# Window Calls (GNOME Shell extension) is the most accurate when installed.
DEFAULT_BACKENDS = (
    GnomeShellWindowCallsBackend(),
    AtspiFocusBackend(),
)
