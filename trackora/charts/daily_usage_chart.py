"""Pyqtgraph chart widget for today's hourly usage."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QFont
import pyqtgraph as pg

from trackora.charts._base import BaseUsageChart


# ── Human-readable hour labels (matching the reference: 12 AM, 3 AM …) ──────
_HOUR_DISPLAY: list[str] = [
    "12 AM", "", "", "3 AM", "", "", "6 AM", "", "",
    "9 AM", "", "", "12 PM", "", "", "3 PM", "", "",
    "6 PM", "", "", "9 PM", "", "",
]


class _MinutesAxis(pg.AxisItem):
    """Left axis that shows values in minutes (input is hours)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        font = QFont()
        font.setPointSize(8)
        self.setTickFont(font)

    def tickStrings(self, values, scale, spacing):
        return [f"{int(v * 60)}m" for v in values]


class DailyUsageChart(BaseUsageChart):
    """Bar chart showing today's usage distribution by hour.

    Styled for ambient, premium dark-theme integration.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(
            min_height=200,
            hint_size=QSize(720, 280),
            parent=parent,
        )
        # Replace the default left axis with one that shows minutes
        minutes_axis = _MinutesAxis(orientation="left")
        minutes_axis.setPen(pg.mkPen(QColor(30, 42, 58, 40), width=1))
        minutes_axis.setTextPen(pg.mkPen(QColor("#566a82")))
        minutes_axis.setStyle(
            tickLength=-4,
            tickTextOffset=6,
        )
        self._plot_item.setAxisItems({"left": minutes_axis})
        self._plot_item.getAxis("top").hide()
        self._plot_item.getAxis("right").hide()

    def update_chart(self, hour_labels: list[str], hour_values: list[float]) -> None:
        """Redraw the hourly usage chart with soft blue bars."""
        display_labels = _HOUR_DISPLAY[: len(hour_labels)]
        self._draw_bars(
            labels=display_labels,
            values=hour_values,
            width=0.50,
            brush_color="#3b82f6",
        )
