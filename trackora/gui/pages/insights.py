"""Insights page — premium analytics and productivity statistics of Trackora."""

from __future__ import annotations

from datetime import timedelta
from collections import defaultdict

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import (
    QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient
)
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget, QGridLayout
)

from trackora.database.dashboard import DashboardRepository
from trackora.models.dashboard import InsightsData, AppUsageSummary

# ── Color tokens ─────────────────────────────────────────────────────────────
_BG = "#0d1117"
_CARD = "#141a23"
_CARD_LIGHTER = "#171f2a"
_CARD_BORDER = "#1c2735"
_TEXT_PRIMARY = "#e6edf5"
_TEXT_SECONDARY = "#8b9bb4"
_TEXT_MUTED = "#566a82"
_ACCENT = "#3b82f6"
_ACCENT_SOFT = "#2563eb"
_GREEN = "#34d399"

_CATEGORY_ICONS = {
    "Browsers": "🌐",
    "Development": "💻",
    "Music": "🎵",
    "Communication": "💬",
    "System": "⚙️",
    "Utilities": "📁",
    "Other": "📦",
}

# ── Icon theme lookup ──────────────────────────────────────────────────────
_ICON_THEME_MAP: dict[str, list[str]] = {
    "VS Code": ["code", "visual-studio-code", "com.visualstudio.code"],
    "Chrome": ["google-chrome", "chromium"],
    "Chromium": ["chromium"],
    "Brave": ["brave-browser"],
    "Firefox": ["firefox"],
    "Spotify": ["spotify"],
    "Discord": ["discord"],
    "Slack": ["slack"],
    "Telegram": ["telegram-desktop", "telegram"],
    "Files": ["org.gnome.Nautilus", "system-file-manager"],
    "Console": ["org.gnome.Console", "utilities-terminal"],
    "Settings": ["org.gnome.Settings", "preferences-system"],
    "Kitty": ["kitty"],
    "Terminal": ["org.gnome.Console", "utilities-terminal", "gnome-terminal"],
    "GitHub Desktop": ["github-desktop"],
    "Cursor": ["co.anysphere.cursor", "cursor"],
}
_FALLBACK_ICON = "application-x-executable"


def _get_app_icon(app_name: str, size: int = 24) -> QPixmap | None:
    """Try to load a native Linux theme icon for the app."""
    candidates = _ICON_THEME_MAP.get(app_name, [app_name.lower().replace(" ", "-")])
    if isinstance(candidates, str):
        candidates = [candidates]
    for name in candidates:
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            return icon.pixmap(QSize(size, size))
    fallback = QIcon.fromTheme(_FALLBACK_ICON)
    if not fallback.isNull():
        return fallback.pixmap(QSize(size, size))
    return None


def _add_shadow(widget: QWidget, blur: int = 24, opacity: int = 40, dy: int = 4):
    """Attach a soft drop shadow to a widget for depth layering."""
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, opacity))
    shadow.setOffset(0, dy)
    widget.setGraphicsEffect(shadow)


def _format_duration_smart(seconds: int) -> str:
    """Format duration in seconds into a friendly string."""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    rem_minutes = minutes % 60
    if rem_minutes == 0:
        return f"{hours}h"
    return f"{hours}h {rem_minutes}m"


def _format_hour_range(hour: int) -> str:
    """Format hour integer into e.g. '3 PM - 4 PM'."""
    def fmt(h):
        h = h % 24
        if h == 0:
            return "12 AM"
        if h < 12:
            return f"{h} AM"
        if h == 12:
            return "12 PM"
        return f"{h - 12} PM"
    return f"{fmt(hour)} - {fmt(hour + 1)}"


# ── Base components ─────────────────────────────────────────────────────────

class _Card(QFrame):
    """Dark rounded card with subtle depth."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dashCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._base_bg = _CARD
        self._hovered = False
        self.setStyleSheet(self._card_css(_CARD))
        _add_shadow(self, blur=20, opacity=35, dy=3)

    def _card_css(self, bg: str) -> str:
        return (
            f"QFrame#dashCard {{ background: {bg}; "
            f"border: 1px solid {_CARD_BORDER}; border-radius: 14px; }}"
        )

    def enterEvent(self, event):
        self._hovered = True
        self.setStyleSheet(self._card_css(_CARD_LIGHTER))

    def leaveEvent(self, event):
        self._hovered = False
        self.setStyleSheet(self._card_css(_CARD))


# ── Stat Cards (Row 1) ──────────────────────────────────────────────────────

class _StatCard(_Card):
    """Metric card used in the top row of the Insights Page."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(6)

        header = QLabel(title.upper())
        header.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        layout.addWidget(header)

        # Middle content row
        self._middle_layout = QHBoxLayout()
        self._middle_layout.setSpacing(8)
        
        self._icon_label = QLabel()
        self._icon_label.setFixedSize(24, 24)
        self._icon_label.setVisible(False)
        self._middle_layout.addWidget(self._icon_label)

        self._val_label = QLabel("—")
        self._val_label.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 18px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        self._middle_layout.addWidget(self._val_label)
        self._middle_layout.addStretch(1)
        layout.addLayout(self._middle_layout)

        # Bottom subtitle label
        self._sub_label = QLabel("")
        self._sub_label.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 11px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._sub_label)

    def set_val(self, val: str, icon_pix: QPixmap | None = None):
        self._val_label.setText(val)
        if icon_pix:
            self._icon_label.setPixmap(icon_pix)
            self._icon_label.setVisible(True)
        else:
            self._icon_label.setVisible(False)

    def set_sub(self, sub: str, is_green: bool = False):
        self._sub_label.setText(sub)
        color = _GREEN if is_green else _TEXT_SECONDARY
        self._sub_label.setStyleSheet(
            f"color: {color}; font-size: 11px; "
            f"background: transparent; border: none;"
        )


# ── Visual Analytics (Row 2) ────────────────────────────────────────────────

class _HorizontalProgress(QWidget):
    """Custom progress line matching Trackora's aesthetics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self._pct = 0

    def set_pct(self, pct: int):
        self._pct = max(0, min(pct, 100))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background track
        painter.setBrush(QBrush(QColor("#1c2735")))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 4, 4)

        # Filled portion
        fill_w = int((self._pct / 100.0) * self.width())
        if fill_w > 0:
            grad = QLinearGradient(0, 0, fill_w, 0)
            grad.setColorAt(0, QColor("#3b82f6"))
            grad.setColorAt(1, QColor("#60a5fa"))
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(0, 0, fill_w, self.height(), 4, 4)
        painter.end()


class _AppRow(QWidget):
    """Horizontal progress row for Usage Distribution chart."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._app_name_label = QLabel()
        self._app_name_label.setFixedWidth(90)
        self._app_name_label.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 12px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._app_name_label)

        self._progress = _HorizontalProgress()
        layout.addWidget(self._progress, 1)

        self._duration_label = QLabel()
        self._duration_label.setFixedWidth(90)
        self._duration_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._duration_label.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 12px; font-weight: 600; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._duration_label)

    def set_data(self, name: str, duration: int, pct: int):
        self._app_name_label.setText(name)
        self._progress.set_pct(pct)
        self._duration_label.setText(f"{_format_duration_smart(duration)} ({pct}%)")


class _HourlyChart(QWidget):
    """Custom premium 24-hour activity vertical bar chart."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(140)
        self._hourly_data: list[int] = [0] * 24
        self._peak_idx = -1
        self._hovered_idx = -1
        self.setMouseTracking(True)

    def set_data(self, data: list[int]):
        self._hourly_data = data
        if any(data):
            self._peak_idx = data.index(max(data))
        else:
            self._peak_idx = -1
        self.update()

    def mouseMoveEvent(self, event):
        pad_side = 20
        chart_w = self.width() - 2 * pad_side
        bar_w = chart_w / 24
        
        pos_x = event.position().x()
        if pad_side <= pos_x <= self.width() - pad_side:
            idx = int((pos_x - pad_side) // bar_w)
            idx = max(0, min(idx, 23))
            if idx != self._hovered_idx:
                self._hovered_idx = idx
                self.update()
        else:
            if self._hovered_idx != -1:
                self._hovered_idx = -1
                self.update()

    def leaveEvent(self, event):
        self._hovered_idx = -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        pad_side = 20
        pad_bottom = 22
        pad_top = 20
        
        w = self.width()
        h = self.height()
        
        chart_w = w - 2 * pad_side
        chart_h = h - pad_top - pad_bottom
        
        max_val = max(self._hourly_data) if any(self._hourly_data) else 1
        
        bar_spacing = 3
        bar_w = (chart_w / 24)
        
        # Guidelines
        guideline_pen = QPen(QColor("#1c2735"), 1, Qt.DashLine)
        painter.setPen(guideline_pen)
        painter.drawLine(pad_side, pad_top, w - pad_side, pad_top)
        painter.drawLine(pad_side, pad_top + chart_h // 2, w - pad_side, pad_top + chart_h // 2)

        font = QFont()
        font.setPixelSize(9)
        painter.setFont(font)

        for i, val in enumerate(self._hourly_data):
            is_peak = (i == self._peak_idx)
            is_hovered = (i == self._hovered_idx)

            bar_height = int((val / max_val) * chart_h) if val > 0 else 2
            bx = pad_side + i * bar_w + bar_spacing // 2
            by = h - pad_bottom - bar_height
            bw = max(2, int(bar_w - bar_spacing))
            
            rect = QRectF(bx, by, bw, bar_height)

            # Glow
            if is_peak or is_hovered:
                glow_cx = rect.center().x()
                glow_cy = rect.top()
                grad = QRadialGradient(glow_cx, glow_cy, rect.height() * 0.8 if rect.height() > 0 else 10)
                grad.setColorAt(0, QColor(59, 130, 246, 30))
                grad.setColorAt(1, QColor(59, 130, 246, 0))
                painter.setBrush(QBrush(grad))
                painter.setPen(Qt.NoPen)
                r = rect.height() * 0.8 if rect.height() > 0 else 10
                painter.drawEllipse(QRectF(glow_cx - r, glow_cy - r * 0.3, r * 2, r * 2))

            # Color gradient
            bar_grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            if is_peak:
                bar_grad.setColorAt(0, QColor("#60a5fa"))
                bar_grad.setColorAt(1, QColor("#3b82f6"))
            elif is_hovered:
                bar_grad.setColorAt(0, QColor(59, 130, 246, 200))
                bar_grad.setColorAt(1, QColor(59, 130, 246, 140))
            else:
                bar_grad.setColorAt(0, QColor(59, 130, 246, 120))
                bar_grad.setColorAt(1, QColor(59, 130, 246, 70))

            path = QPainterPath()
            path.addRoundedRect(rect, 2, 2)
            painter.setBrush(QBrush(bar_grad))
            painter.setPen(Qt.NoPen)
            painter.drawPath(path)

            # Hour markers on x-axis
            if i in [0, 6, 12, 18, 23]:
                label_text = ""
                if i == 0: label_text = "12 AM"
                elif i == 6: label_text = "6 AM"
                elif i == 12: label_text = "12 PM"
                elif i == 18: label_text = "6 PM"
                elif i == 23: label_text = "11 PM"
                
                painter.setPen(QPen(QColor("#8b9bb4" if is_peak else "#566a82")))
                lbl_rect = QRectF(bx - 12, h - pad_bottom + 4, 30, 14)
                painter.drawText(lbl_rect, Qt.AlignCenter, label_text)

        painter.end()


# ── Productivity Summary (Row 3) ────────────────────────────────────────────

class _MetricBlock(QWidget):
    """Single vertical stat blocks grouped in Row 3."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        self._value = QLabel("—")
        self._value.setAlignment(Qt.AlignCenter)
        self._value.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 20px; font-weight: 700; "
            f"background: transparent;"
        )
        layout.addWidget(self._value)

        self._caption = QLabel("")
        self._caption.setAlignment(Qt.AlignCenter)
        self._caption.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 700; "
            f"letter-spacing: 0.08em; background: transparent;"
        )
        layout.addWidget(self._caption)

    def set_data(self, value: str, caption: str):
        self._value.setText(value)
        self._caption.setText(caption.upper())


# ── App Category Breakdown (Row 4) ──────────────────────────────────────────

class _CategoryCard(_Card):
    """Small rounded category breakdown item."""

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.setFixedSize(145, 96)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        
        icon_str = _CATEGORY_ICONS.get(name, "📦")
        self._icon_lbl = QLabel(icon_str)
        self._icon_lbl.setStyleSheet(
            "font-family: 'Segoe UI Emoji', 'Noto Color Emoji', 'Apple Color Emoji', 'Segoe UI Symbol', 'emoji', sans-serif; "
            "font-size: 16px; background: transparent; border: none;"
        )
        header_layout.addWidget(self._icon_lbl)

        name_lbl = QLabel(name.upper())
        name_lbl.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 700; "
            f"letter-spacing: 0.06em; background: transparent; border: none;"
        )
        header_layout.addWidget(name_lbl)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        self._duration_lbl = QLabel("—")
        self._duration_lbl.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 15px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._duration_lbl)

        self._pct_lbl = QLabel("0% of screen time")
        self._pct_lbl.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 11px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._pct_lbl)

    def set_data(self, duration: int, pct: int):
        self._duration_lbl.setText(_format_duration_smart(duration))
        self._pct_lbl.setText(f"{pct}% of screen time")


# ═══════════════════════════════════════════════════════════════════════════
#  INSIGHTS PAGE
# ═══════════════════════════════════════════════════════════════════════════

class InsightsPage(QWidget):
    """Analytical insights derived from telemetry usage patterns."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._repository: DashboardRepository | None = None

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea {{ background: {_BG}; border: none; }}"
            f"QScrollBar:vertical {{ background: {_BG}; width: 5px; margin: 0; }}"
            f"QScrollBar::handle:vertical {{ background: {_CARD_BORDER}; border-radius: 2px; min-height: 30px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}"
        )

        container = QWidget()
        container.setStyleSheet(f"background: {_BG};")
        scroll.setWidget(container)

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        main = QVBoxLayout(container)
        main.setContentsMargins(28, 14, 28, 28)
        main.setSpacing(16)

        # ── Header ──────────────────────────────────────────────────────
        header = QVBoxLayout()
        header.setSpacing(4)

        title = QLabel("Insights")
        title.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 22px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        header.addWidget(title)

        subtitle = QLabel("Understand your productivity patterns")
        subtitle.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 13px; "
            f"background: transparent; border: none;"
        )
        header.addWidget(subtitle)
        main.addLayout(header)

        # ── Row 1: Key Insights ─────────────────────────────────────────
        self._row1_layout = QHBoxLayout()
        self._row1_layout.setSpacing(16)
        
        self._stat_most_used = _StatCard("Most Used App Today")
        self._stat_peak_hour = _StatCard("Peak Activity Hour")
        self._stat_longest_session = _StatCard("Longest Session")
        self._stat_switches = _StatCard("App Switches")

        self._row1_layout.addWidget(self._stat_most_used)
        self._row1_layout.addWidget(self._stat_peak_hour)
        self._row1_layout.addWidget(self._stat_longest_session)
        self._row1_layout.addWidget(self._stat_switches)
        main.addLayout(self._row1_layout)

        # ── Row 2: Visual Analytics ─────────────────────────────────────
        self._row2_layout = QHBoxLayout()
        self._row2_layout.setSpacing(16)

        # Left: Usage Distribution
        self._dist_card = _Card()
        dist_layout = QVBoxLayout(self._dist_card)
        dist_layout.setContentsMargins(24, 20, 24, 20)
        dist_layout.setSpacing(10)

        dist_title = QLabel("USAGE DISTRIBUTION")
        dist_title.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        dist_layout.addWidget(dist_title)
        
        dist_sub = QLabel("Top applications by usage time")
        dist_sub.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 11px; background: transparent; border: none;"
        )
        dist_layout.addWidget(dist_sub)
        dist_layout.addSpacing(4)

        self._app_rows_container = QVBoxLayout()
        self._app_rows_container.setSpacing(10)
        dist_layout.addLayout(self._app_rows_container)
        dist_layout.addStretch(1)

        # Right: Activity by Hour
        self._hourly_card = _Card()
        hourly_layout = QVBoxLayout(self._hourly_card)
        hourly_layout.setContentsMargins(24, 20, 24, 20)
        hourly_layout.setSpacing(4)

        hourly_title = QLabel("ACTIVITY BY HOUR")
        hourly_title.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        hourly_layout.addWidget(hourly_title)
        
        hourly_sub = QLabel("Screen time breakdown across 24 hours")
        hourly_sub.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 11px; background: transparent; border: none;"
        )
        hourly_layout.addWidget(hourly_sub)
        hourly_layout.addSpacing(6)

        self._hourly_chart = _HourlyChart()
        hourly_layout.addWidget(self._hourly_chart)
        
        self._row2_layout.addWidget(self._dist_card, 3)
        self._row2_layout.addWidget(self._hourly_card, 2)
        main.addLayout(self._row2_layout)

        # ── Row 3: Productivity Summary ─────────────────────────────────
        self._summary_card = _Card()
        summary_layout = QVBoxLayout(self._summary_card)
        summary_layout.setContentsMargins(24, 20, 24, 20)
        summary_layout.setSpacing(4)

        summary_title = QLabel("PRODUCTIVITY SUMMARY")
        summary_title.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        summary_layout.addWidget(summary_title)
        
        summary_sub = QLabel("Key productivity indicators and focus periods")
        summary_sub.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 11px; background: transparent; border: none;"
        )
        summary_layout.addWidget(summary_sub)
        summary_layout.addSpacing(10)

        # Grid of blocks
        self._summary_blocks_layout = QHBoxLayout()
        self._summary_blocks_layout.setSpacing(10)
        
        self._block_sessions = _MetricBlock()
        self._block_avg_len = _MetricBlock()
        self._block_active_app = _MetricBlock()
        self._block_active_hours = _MetricBlock()
        self._block_longest_focus = _MetricBlock()

        self._summary_blocks_layout.addWidget(self._block_sessions, 1)
        self._summary_blocks_layout.addWidget(self._make_separator(), 0)
        self._summary_blocks_layout.addWidget(self._block_avg_len, 1)
        self._summary_blocks_layout.addWidget(self._make_separator(), 0)
        self._summary_blocks_layout.addWidget(self._block_active_app, 1)
        self._summary_blocks_layout.addWidget(self._make_separator(), 0)
        self._summary_blocks_layout.addWidget(self._block_active_hours, 1)
        self._summary_blocks_layout.addWidget(self._make_separator(), 0)
        self._summary_blocks_layout.addWidget(self._block_longest_focus, 1)
        
        summary_layout.addLayout(self._summary_blocks_layout)
        main.addWidget(self._summary_card)

        # ── Row 4: App Category Breakdown ───────────────────────────────
        self._category_section_title = QLabel("APP CATEGORY BREAKDOWN")
        self._category_section_title.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        main.addWidget(self._category_section_title)

        self._category_grid_widget = QWidget()
        self._category_grid = QHBoxLayout(self._category_grid_widget)
        self._category_grid.setContentsMargins(0, 0, 0, 0)
        self._category_grid.setSpacing(16)
        main.addWidget(self._category_grid_widget)

        # ── Empty state (shown when insufficient data) ──────────────────
        self._empty_state = QWidget()
        empty_layout = QVBoxLayout(self._empty_state)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(10)
        empty_layout.setContentsMargins(0, 60, 0, 60)

        empty_icon = QLabel("◈")
        empty_icon.setAlignment(Qt.AlignCenter)
        empty_icon.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 40px; background: transparent; border: none;"
        )
        empty_layout.addWidget(empty_icon)

        empty_title = QLabel("Use Trackora a little longer to unlock insights")
        empty_title.setAlignment(Qt.AlignCenter)
        empty_title.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 15px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        empty_layout.addWidget(empty_title)

        empty_sub = QLabel("Analytics will appear here once active application usage is tracked today.")
        empty_sub.setAlignment(Qt.AlignCenter)
        empty_sub.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 12px; background: transparent; border: none;"
        )
        empty_layout.addWidget(empty_sub)

        self._empty_state.setVisible(False)
        main.addWidget(self._empty_state)

        main.addStretch(1)
        self._main_layout = main
        self._container = container

    def set_repository(self, repo: DashboardRepository):
        """Inject shared repository."""
        self._repository = repo

    def refresh_data(self):
        """Compute and render the productivity insights from database."""
        if self._repository is None:
            return

        data = self._repository.load_insights_data()

        if data is None or data.total_sessions_today == 0:
            self._set_ui_visible(False)
            self._empty_state.setVisible(True)
            return

        self._empty_state.setVisible(False)
        self._set_ui_visible(True)

        # 1. Update Stat Cards (Row 1)
        self._stat_most_used.set_val(
            data.most_used_app_name, 
            _get_app_icon(data.most_used_app_name, 24)
        )
        self._stat_most_used.set_sub(
            f"{_format_duration_smart(data.most_used_app_duration)} ({data.most_used_app_percentage}% of screen time)"
        )

        self._stat_peak_hour.set_val(_format_hour_range(data.peak_hour_start))
        self._stat_peak_hour.set_sub(
            f"{_format_duration_smart(data.peak_hour_duration)} active"
        )

        self._stat_longest_session.set_val(
            data.longest_session_app,
            _get_app_icon(data.longest_session_app, 24)
        )
        self._stat_longest_session.set_sub(
            f"Duration: {_format_duration_smart(data.longest_session_duration)}"
        )

        self._stat_switches.set_val(f"{data.switches_today} switches")
        if data.switches_yesterday is not None and data.switches_yesterday > 0:
            diff = data.switches_today - data.switches_yesterday
            pct = int((abs(diff) / data.switches_yesterday) * 100)
            if diff < 0:
                self._stat_switches.set_sub(f"↓ {pct}% from yesterday", is_green=True)
            elif diff > 0:
                self._stat_switches.set_sub(f"↑ {pct}% from yesterday")
            else:
                self._stat_switches.set_sub("Same switches as yesterday")
        else:
            self._stat_switches.set_sub("First day of tracking")

        # 2. Update Usage Distribution (Row 2 Left)
        # Clear previous progress rows
        while self._app_rows_container.count():
            item = self._app_rows_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Add top 5 apps
        top_apps = data.usage_distribution[:5]
        total_top_duration = sum(app_durations.duration_seconds for app_durations in data.usage_distribution)
        for app in top_apps:
            pct = int((app.duration_seconds / total_top_duration) * 100) if total_top_duration > 0 else 0
            row = _AppRow()
            row.set_data(app.app_name, app.duration_seconds, pct)
            self._app_rows_container.addWidget(row)

        # 3. Update Activity by Hour Chart (Row 2 Right)
        self._hourly_chart.set_data(data.hourly_activity)

        # 4. Update Productivity Summary (Row 3)
        self._block_sessions.set_data(str(data.total_sessions_today), "TOTAL SESSIONS")
        self._block_avg_len.set_data(_format_duration_smart(data.avg_session_length_seconds), "AVG SESSION LENGTH")
        self._block_active_app.set_data(data.most_active_app, "MOST ACTIVE APP")
        self._block_active_hours.set_data(f"{data.total_active_hours}h", "ACTIVE HOURS")
        self._block_longest_focus.set_data(_format_duration_smart(data.longest_focus_period_seconds), "LONGEST FOCUS")

        # 5. Update Categories Breakdown (Row 4)
        # Clear category grid layout
        while self._category_grid.count():
            item = self._category_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Add category cards dynamically
        for cat, dur, pct in data.category_breakdown:
            card = _CategoryCard(cat)
            card.set_data(dur, pct)
            self._category_grid.addWidget(card)
        self._category_grid.addStretch(1)

    def _set_ui_visible(self, visible: bool):
        """Toggle visibility of analytical widgets."""
        self._stat_most_used.setVisible(visible)
        self._stat_peak_hour.setVisible(visible)
        self._stat_longest_session.setVisible(visible)
        self._stat_switches.setVisible(visible)
        self._dist_card.setVisible(visible)
        self._hourly_card.setVisible(visible)
        self._summary_card.setVisible(visible)
        self._category_section_title.setVisible(visible)
        self._category_grid_widget.setVisible(visible)

    def _make_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Plain)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background-color: {_CARD_BORDER}; border: none;")
        return sep
