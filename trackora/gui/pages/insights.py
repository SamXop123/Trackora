"""Insights page — placeholder for the upcoming redesign."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class InsightsPage(QWidget):
    """AI-powered / analytical insights derived from usage patterns."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel("Insights — coming soon")
        label.setStyleSheet("color: #8ea1bd; font-size: 14px;")
        layout.addWidget(label)
