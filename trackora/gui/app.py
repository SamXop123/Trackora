"""PySide6 application entrypoint for the Trackora dashboard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from trackora.gui.dashboard_window import DashboardWindow
from trackora.utils.paths import default_database_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="trackora-dashboard",
        description="Trackora desktop dashboard",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="Path to trackora.db (default: XDG data dir / trackora / …).",
    )
    parser.add_argument(
        "--refresh-seconds",
        type=int,
        default=5,
        help="Dashboard refresh interval in seconds (default: 5).",
    )
    args = parser.parse_args(argv)

    app = QApplication(sys.argv if argv is None else [sys.argv[0], *argv])
    app.setApplicationName("Trackora")
    app.setOrganizationName("Trackora")

    database_path = args.database.expanduser() if args.database else default_database_path()
    window = DashboardWindow(
        database_path=database_path,
        refresh_seconds=max(args.refresh_seconds, 2),
    )
    window.show()
    return app.exec()
