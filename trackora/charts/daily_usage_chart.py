"""Pyqtgraph chart widget for today's hourly usage."""

from __future__ import annotations

from PySide6.QtCore import QSize

from trackora.charts._base import BaseUsageChart


class DailyUsageChart(BaseUsageChart):
    """Simple bar chart showing today's usage distribution by hour."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            min_height=360,
            hint_size=QSize(720, 420),
            parent=parent,
        )
        self.getPlotItem().setLabel("left", "Hours", color="#b6c2d9")

    def update_chart(self, hour_labels: list[str], hour_values: list[float]) -> None:
        """Redraw the hourly usage chart."""
        self._draw_bars(
            labels=hour_labels,
            values=hour_values,
            width=0.58,
            brush_color="#4f8cff",
        )
