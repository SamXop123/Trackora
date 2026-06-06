"""Dashboard page — polished premium landing view of Trackora."""

from __future__ import annotations

import math
from datetime import date, datetime

from PySide6.QtCore import (Qt, QRectF, QSize)

from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient,
                           QPainter, QPainterPath, QPen, QPixmap, QRadialGradient)

from PySide6.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
                           QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from ...charts import DailyUsageChart
from ...models.dashboard import (
    ActiveAppStatus, AppUsageSummary, DailyUsageSummary, DashboardSnapshot,
)
from ...utils.formatting import format_duration_compact, format_duration_live
from ...database.dashboard import _get_app_category

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ...database.dashboard import DashboardRepository

# ─── Color tokens ────────────────────────────────────────────────────────────
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
_GREEN_DIM = "#065f46"

# ─── Icon theme lookup ──────────────────────────────────────────────────────
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


# ─── Base card ──────────────────────────────────────────────────────────────

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


# ─── Hero card ──────────────────────────────────────────────────────────────

class _HeroCard(_Card):
    """Large 'Today' screen-time card with concentric ring visualization."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(190)
        self._today_secs = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(6)

        # Header Row: Section Label + Goal Indicator
        hdr_row = QHBoxLayout()
        section = QLabel("TODAY")
        section.setStyleSheet(
            f"color: {_ACCENT}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        hdr_row.addWidget(section)
        hdr_row.addStretch(1)

        self._goal_label = QLabel("Goal: 8h")
        self._goal_label.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 600; "
            f"background: transparent; border: none;"
        )
        hdr_row.addWidget(self._goal_label)
        layout.addLayout(hdr_row)

        self._time_label = QLabel("0m")
        self._time_label.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 52px; font-weight: 800; "
            f"letter-spacing: -0.04em; background: transparent; border: none;"
        )
        layout.addWidget(self._time_label)

        subtitle = QLabel("Today's Screen Time")
        subtitle.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 12px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(subtitle)
        layout.addSpacing(8)

        # Trend badge row
        trend_row = QHBoxLayout()
        self._comparison_label = QLabel("")
        self._comparison_label.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 11px; font-weight: 600; "
            f"background: rgba(255, 255, 255, 0.02); border: 1px solid {_CARD_BORDER}; "
            f"border-radius: 10px; padding: 3px 8px;"
        )
        trend_row.addWidget(self._comparison_label)
        trend_row.addStretch(1)
        layout.addLayout(trend_row)
        layout.addSpacing(12)

        # Bottom metrics row
        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(16)

        self._hero_stat1 = QLabel("—")
        self._hero_stat1.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 13px; font-weight: 700;")
        self._hero_stat1_lbl = QLabel("Screen Time")
        self._hero_stat1_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 600; text-transform: uppercase;")

        self._hero_stat2 = QLabel("—")
        self._hero_stat2.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 13px; font-weight: 700;")
        self._hero_stat2_lbl = QLabel("Top App Focus")
        self._hero_stat2_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 600; text-transform: uppercase;")

        self._hero_stat3 = QLabel("—")
        self._hero_stat3.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 13px; font-weight: 700;")
        self._hero_stat3_lbl = QLabel("Active Apps")
        self._hero_stat3_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 600; text-transform: uppercase;")

        def add_hero_stat(lbl_widget, val_widget):
            box = QVBoxLayout()
            box.setSpacing(2)
            box.addWidget(val_widget)
            box.addWidget(lbl_widget)
            return box

        metrics_row.addLayout(add_hero_stat(self._hero_stat1_lbl, self._hero_stat1))
        
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setFixedHeight(22)
        sep1.setStyleSheet(f"background-color: {_CARD_BORDER}; border: none; width: 1px;")
        metrics_row.addWidget(sep1)

        metrics_row.addLayout(add_hero_stat(self._hero_stat2_lbl, self._hero_stat2))
        
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFixedHeight(22)
        sep2.setStyleSheet(f"background-color: {_CARD_BORDER}; border: none; width: 1px;")
        metrics_row.addWidget(sep2)

        metrics_row.addLayout(add_hero_stat(self._hero_stat3_lbl, self._hero_stat3))
        metrics_row.addStretch(1)

        layout.addLayout(metrics_row)
        layout.addStretch(1)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w - 65, h // 2

        # Ambient glow
        for radius, alpha in [(70, 18), (50, 28), (35, 38)]:
            grad = QRadialGradient(cx, cy, radius)
            grad.setColorAt(0, QColor(59, 130, 246, alpha))
            grad.setColorAt(1, QColor(59, 130, 246, 0))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # Concentric ring arcs — progress indicator feel
        painter.setBrush(Qt.NoBrush)
        # Outer ring (track)
        painter.setPen(QPen(QColor(59, 130, 246, 25), 2.5))
        painter.drawEllipse(QRectF(cx - 28, cy - 28, 56, 56))

        # Progress arc — maps screen time to 0-360° (8h = full)
        progress = min(self._today_secs / (8 * 3600), 1.0)
        if progress > 0.005:
            painter.setPen(QPen(QColor(59, 130, 246, 160), 2.5, Qt.SolidLine, Qt.RoundCap))
            span = int(progress * 360 * 16)
            painter.drawArc(QRectF(cx - 28, cy - 28, 56, 56), 90 * 16, -span)

        # Inner ring
        painter.setPen(QPen(QColor(59, 130, 246, 18), 1.5))
        painter.drawEllipse(QRectF(cx - 18, cy - 18, 36, 36))

        # Center progress text
        pct = int(progress * 100)
        painter.setFont(QFont("Inter", 8, QFont.Bold))
        painter.setPen(QPen(QColor(_TEXT_PRIMARY)))
        painter.drawText(QRectF(cx - 28, cy - 28, 56, 56), Qt.AlignCenter, f"{pct}%")
        painter.end()

    def update_data(self, today_secs: int, yesterday_secs: int, snapshot: DashboardSnapshot | None = None) -> None:
        self._today_secs = today_secs
        self._time_label.setText(format_duration_compact(today_secs))
        self._hero_stat1.setText(format_duration_compact(today_secs))

        if snapshot:
            self._hero_stat3.setText(str(len(snapshot.all_apps)))
            if snapshot.top_apps:
                self._hero_stat2.setText(format_duration_compact(snapshot.top_apps[0].duration_seconds))
            else:
                self._hero_stat2.setText("—")
        else:
            self._hero_stat2.setText("—")
            self._hero_stat3.setText("—")

        if yesterday_secs > 0:
            diff = ((today_secs - yesterday_secs) / yesterday_secs) * 100
            sign = "+" if diff >= 0 else ""
            if diff <= 0:
                color, arrow = _GREEN, "↘"
                bg_color = "rgba(52, 211, 153, 0.1)"
                border_color = "rgba(52, 211, 153, 0.2)"
            else:
                color, arrow = "#f59e0b", "↗"
                bg_color = "rgba(245, 158, 11, 0.1)"
                border_color = "rgba(245, 158, 11, 0.2)"
            self._comparison_label.setText(f"{arrow}  {sign}{diff:.0f}% compared to yesterday")
            self._comparison_label.setStyleSheet(
                f"color: {color}; font-size: 11px; font-weight: 600; "
                f"background: {bg_color}; border: 1px solid {border_color}; "
                f"border-radius: 10px; padding: 3px 8px;"
            )
        else:
            self._comparison_label.setText("First day of tracking")
            self._comparison_label.setStyleSheet(
                f"color: {_TEXT_MUTED}; font-size: 11px; font-weight: 600; "
                f"background: rgba(255, 255, 255, 0.02); border: 1px solid {_CARD_BORDER}; "
                f"border-radius: 10px; padding: 3px 8px;"
            )
        self.update()


# ─── Currently Active card ──────────────────────────────────────────────────

class _ActiveCard(_Card):
    """Shows the currently active application with live elapsed timer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(190)
        self._pulse = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(6)

        # Header with pulsing indicator
        hdr_lo = QHBoxLayout()
        hdr_lo.setSpacing(6)
        hdr_lo.setContentsMargins(0, 0, 0, 0)

        section = QLabel("CURRENTLY ACTIVE")
        section.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        hdr_lo.addWidget(section)

        self._pulse_dot = QLabel("●")
        self._pulse_dot.setStyleSheet(f"color: {_GREEN}; font-size: 12px; background: transparent; border: none;")
        hdr_lo.addWidget(self._pulse_dot)
        hdr_lo.addStretch(1)
        layout.addLayout(hdr_lo)
        layout.addSpacing(6)

        # Icon + app name + category badge row
        name_row = QHBoxLayout()
        name_row.setSpacing(12)

        self._app_icon_label = QLabel()
        self._app_icon_label.setFixedSize(38, 38)
        self._app_icon_label.setStyleSheet(f"border-radius: 8px; border: 1px solid {_CARD_BORDER}; background: {_CARD_LIGHTER};")
        name_row.addWidget(self._app_icon_label)

        v_info = QVBoxLayout()
        v_info.setSpacing(4)

        self._app_label = QLabel("No active session")
        self._app_label.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 22px; font-weight: 800; "
            f"background: transparent; border: none;"
        )
        v_info.addWidget(self._app_label)

        self._category_badge = QLabel("")
        self._category_badge.setStyleSheet(
            f"color: {_ACCENT}; font-size: 10px; font-weight: 700; "
            f"background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); "
            f"border-radius: 8px; padding: 2px 8px;"
        )
        badge_row = QHBoxLayout()
        badge_row.addWidget(self._category_badge)
        badge_row.addStretch(1)
        v_info.addLayout(badge_row)

        name_row.addLayout(v_info, 1)
        layout.addLayout(name_row)

        self._elapsed_label = QLabel("")
        self._elapsed_label.setStyleSheet(
            f"color: {_ACCENT}; font-size: 18px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._elapsed_label)
        layout.addSpacing(4)

        self._window_label = QLabel("Waiting for activity…")
        self._window_label.setWordWrap(True)
        self._window_label.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 11px; font-style: italic; background: transparent; border: none;"
        )
        layout.addWidget(self._window_label)
        layout.addStretch(1)

    def _set_icon(self, app_name: str) -> None:
        pixmap = _get_app_icon(app_name, 38)
        if pixmap:
            self._app_icon_label.setPixmap(pixmap)
        else:
            self._app_icon_label.setText("●")
            self._app_icon_label.setAlignment(Qt.AlignCenter)
            self._app_icon_label.setStyleSheet(
                f"color: {_ACCENT}; font-size: 20px; background: transparent; border: none;"
            )

    def update_data(self, active: ActiveAppStatus | None) -> None:
        if active is None:
            self._app_label.setText("No active session")
            self._elapsed_label.setText("")
            self._window_label.setText("The tracker is idle")
            self._app_icon_label.clear()
            self._category_badge.setVisible(False)
            self._pulse_dot.setVisible(False)
            return

        self._app_label.setText(active.app_name)
        self._elapsed_label.setText(format_duration_live(active.elapsed_seconds))
        self._set_icon(active.app_name)

        # Resolve category
        cat = _get_app_category(active.app_name)
        self._category_badge.setText(cat.upper())
        self._category_badge.setVisible(True)
        self._pulse_dot.setVisible(True)

        # Color badge depending on category
        colors = {
            "Browsers": (_GREEN, "rgba(52, 211, 153, 0.1)", "rgba(52, 211, 153, 0.2)"),
            "Development": (_ACCENT, "rgba(59, 130, 246, 0.1)", "rgba(59, 130, 246, 0.2)"),
            "Music": ("#a855f7", "rgba(168, 85, 247, 0.1)", "rgba(168, 85, 247, 0.2)"),
            "Communication": ("#ec4899", "rgba(236, 72, 153, 0.1)", "rgba(236, 72, 153, 0.2)"),
            "System": (_TEXT_SECONDARY, "rgba(139, 155, 180, 0.1)", "rgba(139, 155, 180, 0.2)"),
            "Utilities": ("#eab308", "rgba(234, 179, 8, 0.1)", "rgba(234, 179, 8, 0.2)"),
        }
        fg, bg, border = colors.get(cat, (_TEXT_MUTED, "rgba(86, 106, 130, 0.1)", "rgba(86, 106, 130, 0.2)"))
        self._category_badge.setStyleSheet(
            f"color: {fg}; font-size: 10px; font-weight: 700; "
            f"background: {bg}; border: 1px solid {border}; "
            f"border-radius: 8px; padding: 2px 8px;"
        )

        # Toggle pulse opacity
        opacity = "ff" if self._pulse else "55"
        self._pulse_dot.setStyleSheet(f"color: #34d399{opacity}; font-size: 12px; background: transparent; border: none;")
        self._pulse = not self._pulse

        title = active.window_title or ""
        if len(title) > 60:
            title = title[:57] + "…"
        self._window_label.setText(f"↳  {title}" if title else "")


# ─── Activity Timeline card ────────────────────────────────────────────────

class _TimelineCard(_Card):
    """Wraps the DailyUsageChart pyqtgraph widget."""

    def __init__(self, chart: DailyUsageChart, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 14)
        layout.setSpacing(8)

        header = QLabel("ACTIVITY TIMELINE")
        header.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        layout.addWidget(header)
        chart.setMinimumHeight(190)
        layout.addWidget(chart, 1)


# ─── Top Applications card ─────────────────────────────────────────────────

class _AppRow(QWidget):
    """Single application row with native icon, name, progress bar, duration."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setCursor(Qt.PointingHandCursor)
        self._hovered = False
        self._bar_ratio = 0.0

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 4, 8, 4)
        row.setSpacing(12)

        # Rank badge
        self._rank_label = QLabel("")
        self._rank_label.setFixedSize(22, 22)
        self._rank_label.setAlignment(Qt.AlignCenter)
        self._rank_label.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 11px; font-weight: 700; "
            f"background: rgba(255, 255, 255, 0.03); border: 1px solid {_CARD_BORDER}; "
            f"border-radius: 11px;"
        )
        row.addWidget(self._rank_label)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(32, 32)
        self._icon_label.setAlignment(Qt.AlignCenter)
        self._icon_label.setStyleSheet("background: transparent; border: none;")
        row.addWidget(self._icon_label)

        mid = QVBoxLayout()
        mid.setContentsMargins(0, 3, 0, 3)
        mid.setSpacing(4)

        self._name = QLabel("")
        self._name.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 13px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        mid.addWidget(self._name)

        self._bar_widget = QWidget()
        self._bar_widget.setFixedHeight(4) # Thicker progress bar
        mid.addWidget(self._bar_widget)
        row.addLayout(mid, 1)

        self._duration = QLabel("")
        self._duration.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._duration.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 12px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        row.addWidget(self._duration)

    def set_data(self, rank: int, name: str, seconds: int, ratio: float) -> None:
        self._rank_label.setText(str(rank))
        # Highlight top rank
        if rank == 1:
            self._rank_label.setStyleSheet(
                f"color: {_ACCENT}; font-size: 11px; font-weight: 800; "
                f"background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); "
                f"border-radius: 11px;"
            )
        else:
            self._rank_label.setStyleSheet(
                f"color: {_TEXT_MUTED}; font-size: 11px; font-weight: 700; "
                f"background: rgba(255, 255, 255, 0.03); border: 1px solid {_CARD_BORDER}; "
                f"border-radius: 11px;"
            )

        self._name.setText(name)
        self._duration.setText(format_duration_compact(seconds))
        self._bar_ratio = max(0.0, min(ratio, 1.0))
        pixmap = _get_app_icon(name, 28)
        if pixmap:
            self._icon_label.setPixmap(pixmap)
        else:
            self._icon_label.setText("●")
            self._icon_label.setStyleSheet(
                f"color: {_ACCENT}; font-size: 14px; background: {_CARD_BORDER}; "
                f"border-radius: 7px; border: none;"
            )
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Hover background
        if self._hovered:
            painter.setBrush(QBrush(QColor(255, 255, 255, 6)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 8, 8)

        # Progress bar
        bw = self._bar_widget
        if bw.width() > 1:
            pos = bw.mapTo(self, bw.rect().topLeft())
            x, y, w, h = pos.x(), pos.y(), bw.width(), bw.height()
            painter.setBrush(QBrush(QColor(_CARD_BORDER)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(x, y, w, h), 2.0, 2.0)
            fill_w = w * self._bar_ratio
            if fill_w > 0:
                grad = QLinearGradient(x, y, x + fill_w, y)
                grad.setColorAt(0, QColor("#2563eb"))
                grad.setColorAt(1, QColor("#60a5fa"))
                painter.setBrush(QBrush(grad))
                painter.drawRoundedRect(QRectF(x, y, fill_w, h), 2.0, 2.0)
        painter.end()


class _TopAppsCard(_Card):
    """Top applications usage list."""

    _MAX_VISIBLE = 5

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 14)
        layout.setSpacing(2)

        header_row = QHBoxLayout()
        title = QLabel("TOP APPLICATIONS")
        title.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        header_row.addWidget(title)
        header_row.addStretch(1)
        layout.addLayout(header_row)
        layout.addSpacing(6)

        self._rows: list[_AppRow] = []
        for _ in range(self._MAX_VISIBLE):
            row = _AppRow()
            row.setVisible(False)
            self._rows.append(row)
            layout.addWidget(row)

        self._more_label = QLabel("")
        self._more_label.setAlignment(Qt.AlignCenter)
        self._more_label.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; padding: 6px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._more_label)
        layout.addStretch(1)

    def update_data(self, apps: list[AppUsageSummary]) -> None:
        max_secs = apps[0].duration_seconds if apps else 1
        for i, row in enumerate(self._rows):
            if i < len(apps):
                ratio = apps[i].duration_seconds / max(max_secs, 1)
                row.set_data(i + 1, apps[i].app_name, apps[i].duration_seconds, ratio)
                row.setVisible(True)
            else:
                row.setVisible(False)
        extra = len(apps) - self._MAX_VISIBLE
        self._more_label.setText(f"+ {extra} more applications" if extra > 0 else "")


# ─── Weekly Activity chart (custom-painted) ────────────────────────────────

def _format_bar_label(seconds: int) -> str:
    """Compact label for bar tops: 42m, 2.4h, etc."""
    if seconds < 60:
        return ""
    if seconds < 3600:
        return f"{seconds // 60}m"
    hours = seconds / 3600
    if hours == int(hours):
        return f"{int(hours)}h"
    return f"{hours:.1f}h"


class _WeeklyChart(QWidget):
    """Custom-painted 7-day bar chart with rounded tops and today highlight."""

    _BAR_RADIUS = 5
    _PAD_TOP = 28       # space for value labels above bars
    _PAD_BOTTOM = 24    # space for weekday labels below bars
    _PAD_SIDE = 16
    _BAR_GAP_RATIO = 0.35  # gap between bars as fraction of slot width

    def __init__(self, parent=None):
        super().__init__(parent)
        self._days: list[DailyUsageSummary] = []
        self._today: date | None = None
        self._hovered_index: int = -1
        self.setMinimumHeight(170)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, days: list[DailyUsageSummary], today: date):
        self._days = days
        self._today = today
        self.update()

    def _bar_rects(self) -> list[QRectF]:
        """Compute bar rectangles for current widget size."""
        if not self._days:
            return []
        n = len(self._days)
        usable_w = self.width() - 2 * self._PAD_SIDE
        usable_h = self.height() - self._PAD_TOP - self._PAD_BOTTOM
        slot_w = usable_w / n
        gap = slot_w * self._BAR_GAP_RATIO
        bar_w = slot_w - gap
        max_secs = max((d.duration_seconds for d in self._days), default=1) or 1

        rects = []
        for i, day in enumerate(self._days):
            ratio = min(day.duration_seconds / max_secs, 1.0)
            bar_h = max(ratio * usable_h, 3)  # minimum 3px for empty days
            x = self._PAD_SIDE + i * slot_w + gap / 2
            y = self._PAD_TOP + usable_h - bar_h
            rects.append(QRectF(x, y, bar_w, bar_h))
        return rects

    def mouseMoveEvent(self, event):
        rects = self._bar_rects()
        new_idx = -1
        for i, r in enumerate(rects):
            if r.adjusted(-4, -self._PAD_TOP, 4, self._PAD_BOTTOM).contains(event.position()):
                new_idx = i
                break
        if new_idx != self._hovered_index:
            self._hovered_index = new_idx
            self.update()

    def leaveEvent(self, event):
        self._hovered_index = -1
        self.update()

    def paintEvent(self, event):
        if not self._days:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rects = self._bar_rects()
        n = len(self._days)
        usable_w = self.width() - 2 * self._PAD_SIDE
        slot_w = usable_w / n

        label_font = QFont()
        label_font.setPixelSize(10)
        label_font.setWeight(QFont.Medium)
        value_font = QFont()
        value_font.setPixelSize(10)
        value_font.setWeight(QFont.Bold)

        for i, (day, rect) in enumerate(zip(self._days, rects)):
            is_today = (self._today is not None and day.day == self._today)
            is_hovered = (i == self._hovered_index)

            # ── Ambient glow for today ──────────────────────────────────
            if is_today:
                glow_cx = rect.center().x()
                glow_cy = rect.top()
                grad = QRadialGradient(glow_cx, glow_cy, rect.height() * 0.9)
                grad.setColorAt(0, QColor(59, 130, 246, 45))
                grad.setColorAt(1, QColor(59, 130, 246, 0))
                painter.setBrush(QBrush(grad))
                painter.setPen(Qt.NoPen)
                r = rect.height() * 0.9
                painter.drawEllipse(QRectF(glow_cx - r, glow_cy - r * 0.3, r * 2, r * 2))

            # ── Bar gradient ────────────────────────────────────────────
            bar_grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            if is_today:
                bar_grad.setColorAt(0, QColor("#60a5fa"))
                bar_grad.setColorAt(1, QColor("#2563eb"))
            elif is_hovered:
                bar_grad.setColorAt(0, QColor(59, 130, 246, 210))
                bar_grad.setColorAt(1, QColor(59, 130, 246, 140))
            else:
                bar_grad.setColorAt(0, QColor(59, 130, 246, 140))
                bar_grad.setColorAt(1, QColor(59, 130, 246, 70))

            # Draw rounded-top bar via clipped path
            path = QPainterPath()
            path.addRoundedRect(rect, self._BAR_RADIUS, self._BAR_RADIUS)
            painter.setBrush(QBrush(bar_grad))
            if is_today:
                painter.setPen(QPen(QColor("#93c5fd"), 1.2))
            else:
                painter.setPen(Qt.NoPen)
            painter.drawPath(path)

            # ── Value label above bar ───────────────────────────────────
            label_text = _format_bar_label(day.duration_seconds)
            if label_text:
                painter.setFont(value_font)
                text_color = QColor(_TEXT_PRIMARY) if is_today else (QColor(_TEXT_SECONDARY) if is_hovered else QColor(_TEXT_MUTED))
                painter.setPen(QPen(text_color))
                label_rect = QRectF(rect.x() - 10, rect.y() - 18, rect.width() + 20, 16)
                painter.drawText(label_rect, Qt.AlignCenter, label_text)

            # ── Weekday label below bar ─────────────────────────────────
            painter.setFont(label_font)
            day_label = day.day.strftime("%a")
            text_color = QColor(_TEXT_PRIMARY) if is_today else QColor(_TEXT_MUTED)
            painter.setPen(QPen(text_color))
            lbl_rect = QRectF(
                self._PAD_SIDE + i * slot_w,
                self.height() - self._PAD_BOTTOM + 4,
                slot_w, 16,
            )
            painter.drawText(lbl_rect, Qt.AlignCenter, day_label)

        painter.end()


class _WeeklyCard(_Card):
    """Weekly Activity card wrapping the custom bar chart."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 14)
        layout.setSpacing(4)

        header_row = QHBoxLayout()
        title = QLabel("WEEKLY ACTIVITY")
        title.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        header_row.addWidget(title)
        header_row.addStretch(1)

        self._total_label = QLabel("")
        self._total_label.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 11px; "
            f"background: transparent; border: none;"
        )
        header_row.addWidget(self._total_label)
        layout.addLayout(header_row)

        subtitle = QLabel("Compare your usage across the last 7 days")
        subtitle.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 11px; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(subtitle)
        layout.addSpacing(4)

        self._chart = _WeeklyChart()
        layout.addWidget(self._chart, 1)

    def update_data(self, days: list[DailyUsageSummary], today: date):
        self._chart.set_data(days, today)
        total = sum(d.duration_seconds for d in days)
        self._total_label.setText(f"{format_duration_compact(total)} total")


# ─── Bottom stats row ───────────────────────────────────────────────────────

class _StatChip(QFrame):
    """Mini card for stats summary."""

    def __init__(self, icon_char: str, caption: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(
            f"QFrame {{ background: rgba(255, 255, 255, 0.015); "
            f"border: 1px solid {_CARD_BORDER}; border-radius: 10px; }}"
        )
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        icon = QLabel(icon_char)
        icon.setStyleSheet(
            f"color: {_ACCENT}; font-size: 18px; background: transparent; border: none;"
        )
        layout.addWidget(icon)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(3)

        self._value = QLabel("—")
        self._value.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 16px; font-weight: 800; "
            f"background: transparent; border: none;"
        )
        text_col.addWidget(self._value)

        cap = QLabel(caption.upper())
        cap.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 700; "
            f"letter-spacing: 0.05em; background: transparent; border: none;"
        )
        text_col.addWidget(cap)
        layout.addLayout(text_col)
        layout.addStretch(1)

    def set_value(self, text: str) -> None:
        self._value.setText(text)

    def enterEvent(self, event):
        self.setStyleSheet(
            f"QFrame {{ background: rgba(255, 255, 255, 0.03); "
            f"border: 1px solid {_ACCENT_SOFT}; border-radius: 10px; }}"
        )

    def leaveEvent(self, event):
        self.setStyleSheet(
            f"QFrame {{ background: rgba(255, 255, 255, 0.015); "
            f"border: 1px solid {_CARD_BORDER}; border-radius: 10px; }}"
        )


class _MetricsCard(_Card):
    """Vertical metrics panel on the right side of Weekly Activity."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("METRICS SUMMARY")
        header.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        layout.addWidget(header)
        layout.addSpacing(4)

        self._stat_screen = _StatChip("◷", "Total Screen Time")
        self._stat_sessions = _StatChip("⊞", "Total Apps")
        self._stat_focused = _StatChip("◎", "Focused Time")

        layout.addWidget(self._stat_screen)
        layout.addWidget(self._stat_sessions)
        layout.addWidget(self._stat_focused)
        layout.addStretch(1)


# ═══════════════════════════════════════════════════════════════════════════
#  DASHBOARD PAGE
# ═══════════════════════════════════════════════════════════════════════════

class DashboardPage(QWidget):
    """Main dashboard page — premium polished version."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._active_status: ActiveAppStatus | None = None
        self._last_snapshot: DashboardSnapshot | None = None

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

        # Date header
        self._date_label = QLabel("")
        self._date_label.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 12px; font-weight: 500; "
            f"background: {_CARD}; border: 1px solid {_CARD_BORDER}; "
            f"border-radius: 8px; padding: 7px 14px;"
        )
        self._date_label.setFixedHeight(34)
        date_row = QHBoxLayout()
        date_row.addWidget(self._date_label)
        date_row.addStretch(1)
        main.addLayout(date_row)

        # Top row: Hero + Active
        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        self._hero_card = _HeroCard()
        top_row.addWidget(self._hero_card, 3)
        self._active_card = _ActiveCard()
        top_row.addWidget(self._active_card, 2)
        main.addLayout(top_row)

        # Middle row: Timeline + Top Apps
        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)
        self._daily_chart = DailyUsageChart()
        self._timeline_card = _TimelineCard(self._daily_chart)
        mid_row.addWidget(self._timeline_card, 3)
        self._top_apps_card = _TopAppsCard()
        mid_row.addWidget(self._top_apps_card, 2)
        main.addLayout(mid_row)

        # Bottom row: Weekly Activity + Metrics Card
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(16)
        self._weekly_card = _WeeklyCard()
        bottom_row.addWidget(self._weekly_card, 3)
        self._metrics_card = _MetricsCard()
        bottom_row.addWidget(self._metrics_card, 2)
        main.addLayout(bottom_row)
        main.addStretch(1)

    def set_repository(self, repository: DashboardRepository) -> None:
        self._repository = repository

    def refresh(self, snapshot: DashboardSnapshot) -> None:
        old_app = self._active_status.app_name if self._active_status else None
        new_app = snapshot.active_app.app_name if snapshot.active_app else None
        if old_app != new_app:
            from trackora.utils.logging import log_info
            log_info(f"Active app updated: {new_app or 'None'}")

        self._last_snapshot = snapshot
        self._active_status = snapshot.active_app
        now = snapshot.last_refreshed
        self._date_label.setText(f"  📅  {now.strftime('%B %d, %Y')}")
        self._hero_card.update_data(snapshot.total_today_seconds, snapshot.total_yesterday_seconds, snapshot)
        self._active_card.update_data(snapshot.active_app)
        self._daily_chart.update_chart(snapshot.hourly_labels, snapshot.hourly_values)
        self._top_apps_card.update_data(snapshot.all_apps)
        self._weekly_card.update_data(snapshot.weekly_days, snapshot.last_refreshed.date())
        
        self._metrics_card._stat_screen.set_value(format_duration_compact(snapshot.total_today_seconds))
        self._metrics_card._stat_sessions.set_value(str(len(snapshot.all_apps)))
        if snapshot.top_apps:
            self._metrics_card._stat_focused.set_value(format_duration_compact(snapshot.top_apps[0].duration_seconds))
        else:
            self._metrics_card._stat_focused.set_value("0m")

    def tick_active_session(self) -> None:
        if not hasattr(self, "_repository") or self._repository is None:
            return

        from trackora.utils.logging import log_info
        
        active = self._repository.load_active_app()
        
        old_app = self._active_status.app_name if self._active_status else None
        new_app = active.app_name if active else None
        
        if old_app != new_app:
            log_info(f"Active app updated: {new_app or 'None'}")
            
        self._active_status = active
        self._active_card.update_data(active)
