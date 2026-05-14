"""CLI: poll the extension-written JSON and print focused app lines."""

from __future__ import annotations

import argparse
import signal
import sys
from pathlib import Path

from trackora.service import run_poll_loop
from trackora.window_state import default_state_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="trackora",
        description=(
            "Trackora backend: print focused app from the Shell extension's "
            "JSON file (extension is the only focus detector)."
        ),
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        help="Seconds between reads (default: 3).",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=None,
        help="Path to current_window.json (default: XDG data dir / trackora / …).",
    )
    args = parser.parse_args(argv)

    if args.interval <= 0:
        print("interval must be positive", file=sys.stderr)
        return 2

    path: Path | None = args.state_file
    if path is None:
        path = default_state_path()
    else:
        path = path.expanduser()

    stop: list[bool] = [False]

    def _handle_sigint(_signum, _frame) -> None:
        stop[0] = True

    signal.signal(signal.SIGINT, _handle_sigint)

    run_poll_loop(
        interval_sec=float(args.interval),
        state_path=path,
        stop_flag=stop,
    )
    return 0
