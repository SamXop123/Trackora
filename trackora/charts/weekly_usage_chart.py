"""Pyqtgraph weekly bar chart for Trackora historical activity."""

from __future__ import annotations

from PySide6.QtCore import QSize
import pyqtgraph as pg

from trackora.charts._base import BaseUsageChart


class WeeklyUsageChart(BaseUsageChart):
    """Bar chart showing total usage for the last 7 days."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            min_height=280,
            hint_size=QSize(520, 320),
            parent=parent,
        )
        self._value_items: list[pg.TextItem] = []
        self.getPlotItem().setLabel("left", "Hours", color="#b6c2d9")

    def update_chart(self, day_labels: list[str], day_values: list[float]) -> None:
        """Redraw the weekly totals chart."""
        self._clear_value_labels()
        self._draw_bars(
            labels=day_labels,
            values=day_values,
            width=0.56,
            brush_color="#6aa9ff",
        )
        for x_position, value in enumerate(day_values):
            label = pg.TextItem(
                text=f"{value:.1f}h" if value > 0 else "0h",
                color="#d6e4ff",
                anchor=(0.5, 1.0),
            )
            self.getPlotItem().addItem(label)
            label.setPos(x_position, max(value, 0.0) + 0.12)
            self._value_items.append(label)

    def _clear_value_labels(self) -> None:
        for item in self._value_items:
            self.getPlotItem().removeItem(item)
        self._value_items.clear()
