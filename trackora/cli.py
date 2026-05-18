"""CLI: run the Trackora SQLite session tracking backend."""

from __future__ import annotations

import argparse
import signal
import sys
from pathlib import Path

from trackora.services import run_tracking_service
from trackora.utils.lock import TrackoraAlreadyRunningError
from trackora.utils.paths import default_database_path, default_state_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="trackora",
        description=(
            "Trackora backend: read the Shell extension JSON state and persist "
            "app sessions into SQLite."
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
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="Path to trackora.db (default: XDG data dir / trackora / …).",
    )
    args = parser.parse_args(argv)

    if args.interval <= 0:
        print("interval must be positive", file=sys.stderr)
        return 2

    state_path: Path | None = args.state_file
    if state_path is None:
        state_path = default_state_path()
    else:
        state_path = state_path.expanduser()

    database_path: Path | None = args.database
    if database_path is None:
        database_path = default_database_path()
    else:
        database_path = database_path.expanduser()

    stop: list[bool] = [False]

    def _handle_sigint(_signum, _frame) -> None:
        stop[0] = True

    signal.signal(signal.SIGINT, _handle_sigint)

    try:
        run_tracking_service(
            interval_sec=float(args.interval),
            state_path=state_path,
            database_path=database_path,
            stop_flag=stop,
        )
    except TrackoraAlreadyRunningError as exc:
        print(f"[Trackora] {exc}", file=sys.stderr)
        return 3
    return 0
