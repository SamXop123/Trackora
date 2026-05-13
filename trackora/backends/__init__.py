"""Detection backends ordered from most specific to most general."""

from trackora.backends.atspi_backend import AtspiFocusBackend
from trackora.backends.gnome_shell_extension import (
    GnomeShellWindowCallsBackend,
)

# Window Calls (GNOME Shell extension) is the most accurate when installed.
DEFAULT_BACKENDS = (
    GnomeShellWindowCallsBackend(),
    AtspiFocusBackend(),
)
