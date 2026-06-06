"""PySide6 application entrypoint for the Trackora dashboard."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Scale the UI up by 40% for better legibility on high-DPI screens
os.environ["QT_SCALE_FACTOR"] = "1.4"

from PySide6.QtWidgets import QApplication

from trackora.gui.dashboard_window import MainWindow
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

    from PySide6.QtGui import QFont, QFontDatabase

    app = QApplication(sys.argv if argv is None else [sys.argv[0], *argv])
    app.setApplicationName("Trackora")
    app.setOrganizationName("Trackora")

    # Load custom premium 'Inter' font from assets folder
    font_path = Path(__file__).resolve().parents[2] / "assets" / "Inter.ttf"
    if font_path.exists():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                app.setFont(QFont(families[0], 10))

    database_path = args.database.expanduser() if args.database else default_database_path()
    window = MainWindow(
        database_path=database_path,
        refresh_seconds=max(args.refresh_seconds, 2),
    )
    window.show()
    return app.exec()
