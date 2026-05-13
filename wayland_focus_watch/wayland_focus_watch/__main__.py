"""Allow ``python3 -m wayland_focus_watch``."""

from wayland_focus_watch.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
