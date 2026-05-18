"""Widget that shows the currently active tracked app."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from trackora.models.dashboard import ActiveAppStatus
from trackora.utils.formatting import format_duration_compact


class ActiveStatusCard(QWidget):
    """Dashboard card for active session status."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
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
        if active is None:
            self._app_label.setText("No active session")
            self._window_label.setText("The tracker is idle or no app has been recorded yet.")
            self._duration_label.setText("Waiting for activity")
            return

        self._app_label.setText(active.app_name)
        self._window_label.setText(active.window_title or "No window title")
        self._duration_label.setText(
            f"Active for {format_duration_compact(active.elapsed_seconds)}"
        )
