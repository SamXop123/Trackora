"""Matplotlib chart widgets for the Trackora dashboard."""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class DailyUsageChart(FigureCanvasQTAgg):
    """Simple bar chart showing today's usage distribution by hour."""

    def __init__(self, parent=None) -> None:
        self._figure = Figure(figsize=(5, 3.8), dpi=100)
        self._axes = self._figure.add_subplot(111)
        super().__init__(self._figure)
        self.setParent(parent)
        self.setMinimumHeight(320)
        self._figure.patch.set_facecolor("#111418")
        self._axes.set_facecolor("#111418")
        self._figure.subplots_adjust(left=0.09, right=0.985, top=0.88, bottom=0.18)

    def update_chart(self, hour_labels: list[str], hour_values: list[float]) -> None:
        """Redraw the hourly usage chart."""
        self._axes.clear()
        self._axes.set_facecolor("#111418")
        self._axes.bar(
            range(len(hour_values)),
            hour_values,
            color="#4f8cff",
            width=0.62,
        )
        self._axes.set_title("Today's Activity Pattern", color="#f3f7ff", fontsize=11, pad=16)
        self._axes.set_xticks(range(len(hour_labels)))
        self._axes.set_xticklabels(hour_labels, rotation=0, fontsize=8, color="#b6c2d9")
        self._axes.tick_params(axis="y", colors="#b6c2d9", labelsize=8)
        self._axes.tick_params(axis="x", colors="#b6c2d9", labelsize=8, pad=6)
        self._axes.spines["top"].set_visible(False)
        self._axes.spines["right"].set_visible(False)
        self._axes.spines["left"].set_color("#243042")
        self._axes.spines["bottom"].set_color("#243042")
        self._axes.grid(axis="y", color="#243042", alpha=0.45, linewidth=0.8)
        self._axes.margins(x=0.02, y=0.15)
        self._axes.set_ylabel("Hours", color="#b6c2d9", fontsize=9)
        self.draw_idle()
