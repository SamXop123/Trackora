"""Table widget for showing today's app usage durations."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from trackora.models.dashboard import AppUsageSummary
from trackora.utils.formatting import format_duration_long


class UsageTableWidget(QTableWidget):
    """Read-only table of today's per-app usage totals."""

    def __init__(self, parent=None) -> None:
        super().__init__(0, 2, parent)
        self.setHorizontalHeaderLabels(["App", "Duration"])
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(False)
        self.setShowGrid(False)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.setMinimumHeight(320)

    def set_rows(self, rows: list[AppUsageSummary]) -> None:
        """Replace the table content with aggregated app usage rows."""
        self.setRowCount(len(rows))
        for row_index, item in enumerate(rows):
            app_item = QTableWidgetItem(item.app_name)
            duration_item = QTableWidgetItem(format_duration_long(item.duration_seconds))
            duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row_index, 0, app_item)
            self.setItem(row_index, 1, duration_item)
