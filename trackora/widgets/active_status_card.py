"""Widget that shows the currently active tracked app."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from trackora.models.dashboard import ActiveAppStatus
from trackora.utils.formatting import format_duration_live
from trackora.utils.settings import settings_manager


class ActiveStatusCard(QWidget):
    """Dashboard card for active session status."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        self._active_status: ActiveAppStatus | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        title = QLabel("Currently Active")
        title.setObjectName("metricTitle")
        layout.addWidget(title)

        self._app_label = QLabel("No active session")
        self._app_label.setObjectName("metricValue")
        self._app_label.setWordWrap(True)
        layout.addWidget(self._app_label)

        self._window_label = QLabel("Start the background service to see live status")
        self._window_label.setObjectName("metricSubtitle")
        self._window_label.setWordWrap(True)
        layout.addWidget(self._window_label)

        self._duration_label = QLabel("0m")
        self._duration_label.setObjectName("activeDuration")
        layout.addWidget(self._duration_label)

        self.setStyleSheet(
            """
            QLabel#metricTitle {
                color: #8ea1bd;
                font-size: 12px;
                font-weight: 600;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }
            QLabel#metricValue {
                color: #f3f7ff;
                font-size: 22px;
                font-weight: 700;
            }
            QLabel#metricSubtitle {
                color: #aab7cb;
                font-size: 13px;
            }
            QLabel#activeDuration {
                color: #4f8cff;
                font-size: 13px;
                font-weight: 600;
            }
            """
        )

    def update_status(self, active: ActiveAppStatus | None) -> None:
        """Refresh the card content."""
        if settings_manager.is_tracking_paused():
            rem = settings_manager.get_pause_remaining_seconds()
            self._app_label.setText("⏸️ Tracking Paused")
            self._window_label.setText("Tracking is temporarily suspended across all apps.")
            if rem == float("inf"):
                self._duration_label.setText("Paused until manually resumed")
            elif rem is not None:
                self._duration_label.setText(f"Paused ({format_duration_live(int(rem))} remaining)")
            else:
                self._duration_label.setText("Paused")
            return

        self._active_status = active
        if active is None:
            self._app_label.setText("No active session")
            self._window_label.setText("The tracker is idle or no app has been recorded yet.")
            self._duration_label.setText("Waiting for activity")
            return

        self._app_label.setText(active.app_name)
        self._window_label.setText(active.window_title or "No window title")
        self._duration_label.setText(
            f"Active for {format_duration_live(active.elapsed_seconds)}"
        )

    def tick(self) -> None:
        """Advance the displayed timer locally between database refreshes."""
        if settings_manager.is_tracking_paused():
            rem = settings_manager.get_pause_remaining_seconds()
            self._app_label.setText("⏸️ Tracking Paused")
            self._window_label.setText("Tracking is temporarily suspended across all apps.")
            if rem == float("inf"):
                self._duration_label.setText("Paused until manually resumed")
            elif rem is not None:
                self._duration_label.setText(f"Paused ({format_duration_live(int(rem))} remaining)")
            else:
                self._duration_label.setText("Paused")
            return

        if self._active_status is None:
            return

        next_elapsed = self._active_status.elapsed_seconds + 1
        self._active_status = ActiveAppStatus(
            app_name=self._active_status.app_name,
            window_title=self._active_status.window_title,
            started_at=self._active_status.started_at,
            elapsed_seconds=next_elapsed,
        )
        self._duration_label.setText(
            f"Active for {format_duration_live(next_elapsed)}"
        )
