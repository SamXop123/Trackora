"""Weekly bar chart for Trackora historical activity."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class WeeklyUsageChart(FigureCanvasQTAgg):
    """Bar chart showing total usage for the last 7 days."""

    def __init__(self, parent=None) -> None:
        self._figure = Figure(figsize=(5.4, 3.6), dpi=100)
        self._axes = self._figure.add_subplot(111)
        super().__init__(self._figure)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(280)
        self._figure.patch.set_facecolor("#111418")
        self._axes.set_facecolor("#111418")
        self._figure.subplots_adjust(left=0.1, right=0.985, top=0.88, bottom=0.24)

    def sizeHint(self) -> QSize:
        return QSize(520, 320)

    def update_chart(self, day_labels: list[str], day_values: list[float]) -> None:
        """Redraw the weekly totals chart."""
        self._axes.clear()
        self._axes.set_facecolor("#111418")
        bars = self._axes.bar(
            range(len(day_values)),
            day_values,
            color="#6aa9ff",
            width=0.58,
        )
        self._axes.set_title("Last 7 Days", color="#f3f7ff", fontsize=11, pad=14)
        self._axes.set_xticks(range(len(day_labels)))
        self._axes.set_xticklabels(day_labels, fontsize=8, color="#b6c2d9")
        self._axes.tick_params(axis="y", colors="#b6c2d9", labelsize=8, pad=6)
        self._axes.tick_params(axis="x", colors="#b6c2d9", labelsize=8, pad=8)
        self._axes.spines["top"].set_visible(False)
        self._axes.spines["right"].set_visible(False)
        self._axes.spines["left"].set_color("#243042")
        self._axes.spines["bottom"].set_color("#243042")
        self._axes.grid(axis="y", color="#243042", alpha=0.4, linewidth=0.8)
        self._axes.margins(x=0.03, y=0.18)
        self._axes.set_ylabel("Hours", color="#b6c2d9", fontsize=9)

        for bar, value in zip(bars, day_values):
            self._axes.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{value:.1f}h" if value > 0 else "0h",
                ha="center",
                va="bottom",
                color="#d6e4ff",
                fontsize=7,
            )
        self.draw_idle()
