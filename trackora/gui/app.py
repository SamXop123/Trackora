"""PySide6 application entrypoint for the Trackora dashboard."""

from __future__ import annotations

import argparse
import os
import sys
import subprocess
import time
from pathlib import Path

# Scale the UI up by 40% for better legibility on high-DPI screens
os.environ["QT_SCALE_FACTOR"] = "1.4"

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
)

from trackora.gui.dashboard_window import MainWindow
from trackora.utils.paths import default_database_path, get_asset_path

# Styling constants matching Trackora's premium dark mode theme
_BG = "#0d1117"
_CARD = "#141a23"
_TEXT_PRIMARY = "#e6edf5"
_TEXT_SECONDARY = "#8b9bb4"
_ACCENT = "#3b82f6"
_RED = "#ef4444"
_GREEN = "#34d399"


def is_service_active() -> bool:
    """Check if the Trackora background service/daemon is active."""
    import sys
    if sys.platform == "win32":
        try:
            from windows.daemon import is_service_active_win
            return is_service_active_win()
        except Exception:
            return False

    try:
        res = subprocess.run(
            ["systemctl", "--user", "is-active", "--quiet", "trackora.service"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return res.returncode == 0
    except Exception:
        return False


def try_start_service() -> bool:
    """Try to start the background service/daemon automatically."""
    import sys
    if sys.platform == "win32":
        try:
            from windows.daemon import try_start_service_win
            return try_start_service_win()
        except Exception:
            return False

    try:
        # Enable so it starts on login
        subprocess.run(
            ["systemctl", "--user", "enable", "trackora.service"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        # Start the service
        subprocess.run(
            ["systemctl", "--user", "start", "trackora.service"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        # Wait a bit for it to spin up
        for _ in range(5):
            time.sleep(0.2)
            if is_service_active():
                return True
    except Exception:
        pass
    return False


class ServiceStatusDialog(QDialog):
    """Custom styled dialog shown when the background tracking service is not active."""

    def __init__(self, parent: QDialog | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Trackora Service Not Running")
        self.setFixedSize(450, 260)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
        )
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {_BG};
                border: 1px solid #1c2735;
            }}
            QLabel {{
                color: {_TEXT_PRIMARY};
            }}
            QPushButton {{
                background-color: {_CARD};
                color: {_TEXT_PRIMARY};
                border: 1px solid #1c2735;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #171f2a;
                border-color: {_ACCENT};
            }}
            QPushButton#primaryBtn {{
                background-color: {_ACCENT};
                color: #ffffff;
                border: 1px solid #2563eb;
            }}
            QPushButton#primaryBtn:hover {{
                background-color: #2563eb;
            }}
            QTextEdit {{
                background-color: #090d13;
                color: {_TEXT_SECONDARY};
                border: 1px solid #1c2735;
                border-radius: 4px;
                font-family: monospace;
                font-size: 11px;
            }}
        """)

        # Main Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Row
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        self.icon_label = QLabel("⚠️")
        self.icon_label.setStyleSheet("font-size: 28px; background: transparent;")
        header_layout.addWidget(self.icon_label)

        title_label = QLabel("Trackora Service Not Running")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent;")
        header_layout.addWidget(title_label, 1)

        layout.addLayout(header_layout)

        # Body Message Text
        self.msg_label = QLabel(
            "Trackora's background tracking service is currently stopped.\n"
            "Tracking data cannot be collected until the service is running."
        )
        self.msg_label.setWordWrap(True)
        self.msg_label.setStyleSheet(f"color: {_TEXT_SECONDARY}; font-size: 13px; line-height: 1.4;")
        layout.addWidget(self.msg_label, 1)

        # Log Viewer (Collapsed by default, shown on failure/expand)
        self.log_viewer = QTextEdit()
        self.log_viewer.setReadOnly(True)
        self.log_viewer.setVisible(False)
        layout.addWidget(self.log_viewer)

        # Buttons Bar Layout
        self.buttons_layout = QHBoxLayout()
        self.buttons_layout.setSpacing(12)
        self.buttons_layout.addStretch()

        self.view_logs_btn = QPushButton("View Logs")
        self.view_logs_btn.setVisible(False)
        self.view_logs_btn.clicked.connect(self._toggle_logs)
        self.buttons_layout.addWidget(self.view_logs_btn)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.clicked.connect(self.reject)
        self.buttons_layout.addWidget(self.exit_btn)

        self.start_btn = QPushButton("Start Service")
        self.start_btn.setObjectName("primaryBtn")
        self.start_btn.clicked.connect(self._start_service)
        self.buttons_layout.addWidget(self.start_btn)

        layout.addLayout(self.buttons_layout)

    def _start_service(self) -> None:
        """Trigger start on background service/daemon."""
        self.start_btn.setEnabled(False)
        self.exit_btn.setEnabled(False)
        self.msg_label.setStyleSheet(f"color: {_TEXT_SECONDARY}; font-size: 13px;")
        self.msg_label.setText("Attempting to start Trackora service, please wait...")
        QApplication.processEvents()

        try:
            import sys
            if sys.platform == "win32":
                try_start_service()
            else:
                # Start service once for the current session (Never use "enable")
                subprocess.run(
                    ["systemctl", "--user", "start", "trackora.service"],
                    capture_output=True,
                    check=False,
                )

            # Wait briefly for status propagation
            time.sleep(1.5)
            if is_service_active():
                self.msg_label.setStyleSheet(f"color: {_GREEN}; font-size: 13px;")
                self.msg_label.setText("✔ Service started successfully! Launching dashboard...")
                QApplication.processEvents()
                time.sleep(0.8)
                self.accept()
                return
        except Exception:
            pass

        # Failure handling
        self.msg_label.setStyleSheet(f"color: {_RED}; font-size: 13px;")
        import sys
        if sys.platform == "win32":
            self.msg_label.setText(
                "Error: Failed to start background tracking daemon.\n"
                "Please view daemon logs below."
            )
        else:
            self.msg_label.setText(
                "Error: Failed to start background tracking service.\n"
                "Please check systemd configuration or view logs below."
            )
        self.icon_label.setText("❌")

        # Fetch recent logs for failure diagnosing
        try:
            import sys
            if sys.platform == "win32":
                from trackora.utils.paths import default_log_path
                log_path = default_log_path()
                if log_path.exists():
                    content = log_path.read_text(encoding="utf-8")
                    lines = content.splitlines()[-20:]
                    logs = "\n".join(lines)
                else:
                    logs = "No service logs found."
            else:
                res = subprocess.run(
                    ["journalctl", "--user", "-u", "trackora.service", "-n", "20", "--no-pager"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                logs = res.stdout if res.stdout else "No service logs found."
        except Exception as e:
            logs = f"Failed to retrieve service logs: {e}"

        self.log_viewer.setPlainText(logs)

        # Expand UI dimensions to fit log viewer
        self.setFixedSize(500, 420)
        self.log_viewer.setVisible(True)
        self.view_logs_btn.setVisible(True)
        self.view_logs_btn.setText("Hide Logs")

        self.start_btn.setText("Try Again")
        self.start_btn.setEnabled(True)
        self.exit_btn.setEnabled(True)

    def _toggle_logs(self) -> None:
        """Expand or collapse the log viewer frame."""
        visible = self.log_viewer.isVisible()
        self.log_viewer.setVisible(not visible)
        if visible:
            self.setFixedSize(450, 260)
            self.view_logs_btn.setText("View Logs")
        else:
            self.setFixedSize(500, 420)
            self.view_logs_btn.setText("Hide Logs")


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

    from trackora.utils.lock import TrackoraInstanceLock
    from trackora.utils.paths import default_gui_lock_path

    # Enforce single-instance lock for the GUI
    gui_lock = TrackoraInstanceLock(default_gui_lock_path())
    if not gui_lock.acquire():
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv if argv is None else [sys.argv[0], *argv])
        from PySide6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Trackora Already Running")
        msg.setText("Another instance of the Trackora Dashboard is already running.")
        msg.setInformativeText("Please check your system tray or task manager.")
        logo_path = get_asset_path("trackora_logo.png")
        if logo_path.exists():
            from PySide6.QtGui import QIcon
            msg.setWindowIcon(QIcon(str(logo_path)))
        msg.exec()
        return 0

    from PySide6.QtGui import QFont, QFontDatabase, QIcon

    app = QApplication(sys.argv if argv is None else [sys.argv[0], *argv])
    app.setApplicationName("Trackora")
    app.setOrganizationName("Trackora")
    app.setDesktopFileName("trackora")

    # Set application-level window icon
    logo_path = get_asset_path("trackora_logo.png")
    if logo_path.exists():
        app.setWindowIcon(QIcon(str(logo_path)))

    # Load custom premium 'Inter' font from assets folder
    font_path = get_asset_path("Inter.ttf")
    if font_path.exists():
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                app.setFont(QFont(families[0], 10))

    # Ensure GNOME Shell extension is enabled (Linux only)
    if sys.platform != "win32":
        try:
            subprocess.run(
                ["gnome-extensions", "enable", "trackora@trackora.dev"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except Exception:
            pass

    print("[DEBUG] Main entrypoint reached", flush=True)
    # Verification: Verify background tracking service is running (auto-starting if not)
    active1 = is_service_active()
    print(f"[DEBUG] is_service_active 1: {active1}", flush=True)
    if not active1:
        started = try_start_service()
        print(f"[DEBUG] try_start_service result: {started}", flush=True)

    # Allow time for status propagation (Windows daemon process startup)
    if sys.platform == "win32" and not active1:
        print("[DEBUG] Waiting 1.0 seconds for daemon to initialize...", flush=True)
        time.sleep(1.0)

    active2 = is_service_active()
    print(f"[DEBUG] is_service_active 2: {active2}", flush=True)
    if not active2:
        print("[DEBUG] Showing ServiceStatusDialog...", flush=True)
        dialog = ServiceStatusDialog()
        res = dialog.exec()
        print(f"[DEBUG] dialog.exec returned: {res}", flush=True)
        if res != QDialog.DialogCode.Accepted:
            print("[DEBUG] Dialog not accepted. Exiting with 0.", flush=True)
            return 0

    print("[DEBUG] Initializing MainWindow...", flush=True)
    database_path = args.database.expanduser() if args.database else default_database_path()
    print(f"[DEBUG] Database path: {database_path}", flush=True)
    window = MainWindow(
        database_path=database_path,
        refresh_seconds=max(args.refresh_seconds, 2),
    )
    print("[DEBUG] Showing MainWindow...", flush=True)
    window.show()
    print("[DEBUG] Running app.exec()...", flush=True)
    ret = app.exec()
    print(f"[DEBUG] app.exec finished with: {ret}", flush=True)
    return ret
