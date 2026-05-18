"""Shared pyqtgraph chart helpers for the Trackora dashboard."""

from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QSizePolicy
import pyqtgraph as pg


pg.setConfigOptions(antialias=True)


class BaseUsageChart(pg.PlotWidget):
    """Common styling and behavior for Trackora bar charts."""

    _BASELINE_PADDING = 0.08
    _TOP_PADDING_RATIO = 0.18

    def __init__(self, *, min_height: int, hint_size: QSize, parent=None) -> None:
        super().__init__(parent=parent)
        self._hint_size = hint_size
        self._bar_item: pg.BarGraphItem | None = None
        self._plot_item = self.getPlotItem()
        self._view_box = self._plot_item.getViewBox()

        self.setBackground("#111418")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(min_height)

        self._plot_item.setMenuEnabled(False)
        self.setMenuEnabled(False)
        self._plot_item.hideButtons()
        self._view_box.setMouseEnabled(x=False, y=False)
        self._view_box.setDefaultPadding(0.0)
        self._view_box.enableAutoRange(x=False, y=False)
        self._plot_item.showGrid(x=False, y=True, alpha=0.18)
        self._plot_item.layout.setContentsMargins(10, 8, 6, 8)
        self._plot_item.layout.setHorizontalSpacing(8)
        self._plot_item.layout.setVerticalSpacing(6)

        axis_font = QFont()
        axis_font.setPointSize(8)

        for axis_name in ("left", "bottom"):
            axis = self._plot_item.getAxis(axis_name)
            axis.setPen(pg.mkPen("#243042", width=1))
            axis.setTextPen(pg.mkPen("#b6c2d9"))
            axis.setTickFont(axis_font)
            axis.setStyle(
                autoExpandTextSpace=True,
                hideOverlappingLabels=False,
                tickTextOffset=10,
            )

        self._plot_item.getAxis("top").hide()
        self._plot_item.getAxis("right").hide()
        self._plot_item.setContentsMargins(0, 0, 0, 0)

    def sizeHint(self) -> QSize:
        return self._hint_size

    def _draw_bars(
        self,
        *,
        labels: list[str],
        values: list[float],
        width: float,
        brush_color: str,
    ) -> None:
        self._plot_item.clear()

        normalized_labels = [label.replace("\n", " ") for label in labels]
        x_positions = list(range(len(values)))
        heights = [max(float(value), 0.0) for value in values]

        if heights:
            self._bar_item = pg.BarGraphItem(
                x=x_positions,
                y0=0,
                height=heights,
                width=width,
                brush=pg.mkBrush(QColor(brush_color)),
                pen=pg.mkPen(QColor(brush_color).lighter(110), width=1),
            )
            self._plot_item.addItem(self._bar_item)

        bottom_axis = self._plot_item.getAxis("bottom")
        bottom_axis.setTicks([list(zip(x_positions, normalized_labels))])

        y_max = max(heights, default=0.0)
        baseline_padding = max(y_max * self._BASELINE_PADDING, 0.06)
        padded_y = max(1.0, y_max * (1 + self._TOP_PADDING_RATIO))
        self._plot_item.setXRange(-0.65, max(len(values) - 0.35, 0.65), padding=0)
        self._plot_item.setYRange(-baseline_padding, padded_y, padding=0)
        self._view_box.setLimits(
            xMin=-1.0,
            xMax=max(len(values), 1),
            yMin=-baseline_padding,
            yMax=max(padded_y, 1.0),
        )
