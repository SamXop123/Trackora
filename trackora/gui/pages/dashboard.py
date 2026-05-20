"""Dashboard page — the main landing view of Trackora.

Closely follows the reference design with:
- Hero card (Today's Screen Time, large typography, comparison %)
- Currently Active card (live app, elapsed time, window title)
- Activity Timeline (pyqtgraph bar chart)
- Top Applications (list with progress bars)
- Bottom stats row (total screen time, total sessions, focused time)
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from trackora.charts import DailyUsageChart
from trackora.models.dashboard import ActiveAppStatus, AppUsageSummary, DashboardSnapshot
from trackora.utils.formatting import (
    format_duration_compact,
    format_duration_live,
)


# ─── Color tokens ────────────────────────────────────────────────────────────
_BG = "#0d1117"
_CARD = "#141a23"
_CARD_BORDER = "#1e2a3a"
_TEXT_PRIMARY = "#e6edf5"
_TEXT_SECONDARY = "#8b9bb4"
_TEXT_MUTED = "#5a6a80"
_ACCENT = "#3b82f6"
_ACCENT_DIM = "#2563eb"
_GREEN = "#34d399"
_SURFACE_HOVER = "#1a2332"


# ─── Reusable card frame ────────────────────────────────────────────────────

class _Card(QFrame):
    """Dark rounded card matching the reference design."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dashCard")
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(
            f"""
            QFrame#dashCard {{
                background: {_CARD};
                border: 1px solid {_CARD_BORDER};
                border-radius: 16px;
            }}
            """
        )


# ─── Hero card ──────────────────────────────────────────────────────────────

class _HeroCard(_Card):
    """Large 'Today' screen-time card with decorative glow."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(6)

        # Section label
        section = QLabel("TODAY")
        section.setStyleSheet(f"color: {_ACCENT}; font-size: 11px; font-weight: 700; letter-spacing: 0.1em; background: transparent; border: none;")
        layout.addWidget(section)

        # Big time
        self._time_label = QLabel("0m")
        self._time_label.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 42px; font-weight: 800; letter-spacing: -0.02em; background: transparent; border: none;")
        layout.addWidget(self._time_label)

        # Subtitle
        subtitle = QLabel("Today's Screen Time")
        subtitle.setStyleSheet(f"color: {_TEXT_SECONDARY}; font-size: 13px; background: transparent; border: none;")
        layout.addWidget(subtitle)

        layout.addSpacing(8)

        # Comparison
        self._comparison_label = QLabel("")
        self._comparison_label.setStyleSheet(f"color: {_GREEN}; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(self._comparison_label)

        layout.addStretch(1)

    def paintEvent(self, event):
        """Draw subtle ambient blue glow in top-right corner."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w - 60, 70
        gradient = QRadialGradient(cx, cy, 80)
        gradient.setColorAt(0, QColor(59, 130, 246, 50))
        gradient.setColorAt(0.5, QColor(59, 130, 246, 20))
        gradient.setColorAt(1.0, QColor(59, 130, 246, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(cx - 80, cy - 80, 160, 160))
        # Small clock circle
        painter.setBrush(QBrush(QColor(59, 130, 246, 60)))
        painter.drawEllipse(QRectF(cx - 24, cy - 24, 48, 48))
        painter.end()

    def update_data(self, today_secs: int, yesterday_secs: int) -> None:
        self._time_label.setText(format_duration_compact(today_secs))
        if yesterday_secs > 0:
            diff = ((today_secs - yesterday_secs) / yesterday_secs) * 100
            sign = "+" if diff >= 0 else ""
            color = _GREEN if diff <= 0 else "#f59e0b"
            self._comparison_label.setText(f"↗  {sign}{diff:.0f}% compared to yesterday")
            self._comparison_label.setStyleSheet(f"color: {color}; font-size: 12px; background: transparent; border: none;")
        else:
            self._comparison_label.setText("")


# ─── Currently Active card ──────────────────────────────────────────────────

class _ActiveCard(_Card):
    """Shows the currently active application with live elapsed timer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(8)

        # Section label
        section = QLabel("CURRENTLY ACTIVE")
        section.setStyleSheet(f"color: {_GREEN}; font-size: 11px; font-weight: 700; letter-spacing: 0.1em; background: transparent; border: none;")
        layout.addWidget(section)

        layout.addSpacing(4)

        # App name
        self._app_label = QLabel("No active session")
        self._app_label.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 20px; font-weight: 700; background: transparent; border: none;")
        layout.addWidget(self._app_label)

        # Elapsed time
        self._elapsed_label = QLabel("")
        self._elapsed_label.setStyleSheet(f"color: {_ACCENT}; font-size: 16px; font-weight: 600; background: transparent; border: none;")
        layout.addWidget(self._elapsed_label)

        layout.addSpacing(4)

        # Window title / category
        self._window_label = QLabel("Waiting for activity…")
        self._window_label.setWordWrap(True)
        self._window_label.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px; background: transparent; border: none;")
        layout.addWidget(self._window_label)

        layout.addStretch(1)

    def update_data(self, active: ActiveAppStatus | None) -> None:
        if active is None:
            self._app_label.setText("No active session")
            self._elapsed_label.setText("")
            self._window_label.setText("The tracker is idle")
            return
        self._app_label.setText(active.app_name)
        self._elapsed_label.setText(format_duration_live(active.elapsed_seconds))
        title = active.window_title or "No window title"
        # Show a truncated title
        if len(title) > 60:
            title = title[:57] + "…"
        self._window_label.setText(f"◇  {title}")


# ─── Activity Timeline card ────────────────────────────────────────────────

class _TimelineCard(_Card):
    """Wraps the DailyUsageChart pyqtgraph widget."""

    def __init__(self, chart: DailyUsageChart, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 16)
        layout.setSpacing(10)

        header = QLabel("ACTIVITY TIMELINE")
        header.setStyleSheet(f"color: {_TEXT_SECONDARY}; font-size: 11px; font-weight: 700; letter-spacing: 0.1em; background: transparent; border: none;")
        layout.addWidget(header)

        chart.setMinimumHeight(200)
        layout.addWidget(chart, 1)


