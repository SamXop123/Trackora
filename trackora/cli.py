"""CLI entry: poll interval and stdout formatting."""

from __future__ import annotations

import argparse
import signal
import sys
import time

from trackora.detector import FocusDetector
from trackora.format_output import format_focus_line


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="trackora",
        description="Trackora: print the focused GNOME/Wayland application every few seconds.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        help="Seconds between samples (default: 3).",
    )
    args = parser.parse_args(argv)

    if args.interval <= 0:
        print("interval must be positive", file=sys.stderr)
        return 2

    detector = FocusDetector()
    stop = False

    def _handle_sigint(_signum, _frame) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, _handle_sigint)

    while not stop:
        app, title = detector.snapshot()
        print(format_focus_line(app, title), flush=True)
        # Sleep in slices so Ctrl+C remains responsive for long intervals.
        remaining = float(args.interval)
        step = min(0.2, remaining)
        while remaining > 0 and not stop:
            time.sleep(step)
            remaining -= step

    return 0
