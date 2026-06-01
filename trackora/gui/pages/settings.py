"""Settings page — placeholder for the upcoming redesign."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QFrame


class SettingsPage(QWidget):
    """Application preferences: refresh interval, theme, notifications, etc."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        
        # Premium dark styling consistent with Trackora design tokens
        self.setStyleSheet("background: #0d1117;")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # 1. Large, premium custom logo
        self._logo_label = QLabel()
        self._logo_label.setAlignment(Qt.AlignCenter)
        self._logo_label.setStyleSheet("background: transparent; border: none;")
        
        logo_path = Path(__file__).resolve().parents[3] / "assets" / "trackora_logo.png"
        if logo_path.exists():
            px = QPixmap(str(logo_path))
            self._logo_label.setPixmap(px.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            # Fallback graphic
            self._logo_label.setText("◉")
            self._logo_label.setStyleSheet("color: #3b82f6; font-size: 48px; font-weight: 700; background: transparent;")
            
        layout.addWidget(self._logo_label)

        # 2. Typography headers
        title = QLabel("Trackora")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #e6edf5; font-size: 24px; font-weight: 800; background: transparent; border: none; letter-spacing: 0.05em;")
        layout.addWidget(title)

        version = QLabel("Version 1.0.0 (Premium Release)")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #3b82f6; font-size: 12px; font-weight: 700; background: transparent; border: none; letter-spacing: 0.1em; text-transform: uppercase;")
        layout.addWidget(version)

        # Spacer
        layout.addSpacing(10)

        # 3. High-fidelity brand about card
        about_card = QFrame()
        about_card.setFixedWidth(420)
        about_card.setStyleSheet(
            "QFrame { "
            "  background: #161b22; "
            "  border: 1px solid #30363d; "
            "  border-radius: 14px; "
            "}"
        )
        
        card_lo = QVBoxLayout(about_card)
        card_lo.setContentsMargins(28, 24, 28, 24)
        card_lo.setSpacing(12)

        about_desc = QLabel(
            "Trackora is a premium open-source application telemetry "
            "and focus tracking suite designed to measure focus, analyze "
            "habits, and help you build meaningful digital workflows."
        )
        about_desc.setWordWrap(True)
        about_desc.setAlignment(Qt.AlignCenter)
        about_desc.setStyleSheet("color: #8b9bb4; font-size: 13px; font-weight: 500; line-height: 1.6; background: transparent; border: none;")
        card_lo.addWidget(about_desc)

        layout.addWidget(about_card)

        # Footer notes
        footer = QLabel("Settings & Preferences • Coming Soon")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #566a82; font-size: 11px; font-weight: 600; background: transparent; border: none; letter-spacing: 0.08em; text-transform: uppercase;")
        layout.addWidget(footer)
