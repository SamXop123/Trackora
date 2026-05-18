"""Simple stat card widgets for the dashboard."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class MetricCard(QWidget):
    """Reusable metric display card."""

    def __init__(self, *, title: str, value: str, subtitle: str, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(10)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("metricTitle")
        layout.addWidget(self._title_label)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("metricValue")
        layout.addWidget(self._value_label)

        self._subtitle_label = QLabel(subtitle)
        self._subtitle_label.setObjectName("metricSubtitle")
        self._subtitle_label.setWordWrap(True)
        layout.addWidget(self._subtitle_label)

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
            """
        )

    def set_content(self, *, value: str, subtitle: str) -> None:
        """Update the card's main value and supporting text."""
        self._value_label.setText(value)
        self._subtitle_label.setText(subtitle)
