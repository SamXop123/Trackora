"""Dashboard page — polished premium landing view of Trackora."""

from __future__ import annotations

import math
import os
from datetime import date, datetime

from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QEvent, QPoint, QPropertyAnimation, QRect, QRectF, QSize, QTimer, Qt, Signal, QDate

from PySide6.QtGui import (QBrush, QColor, QFont, QIcon, QLinearGradient,
                           QPainter, QPainterPath, QPen, QPixmap, QRadialGradient)

from PySide6.QtWidgets import (QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
                           QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
                           QStackedWidget, QPushButton, QDialog, QCalendarWidget)

from ...charts import DailyUsageChart
from ...models.dashboard import (
    ActiveAppStatus, AppUsageSummary, DailyUsageSummary, DashboardSnapshot,
)
from ...utils.formatting import format_duration_compact, format_duration_live
from ...database.dashboard import _get_app_category
from ...utils.paths import get_asset_path

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

_CALENDAR_SVG_PATH = str(get_asset_path("calendar.svg")).replace("\\", "/")

from trackora.gui.utils import get_app_icon as _get_app_icon


def _add_shadow(widget: QWidget, blur: int = 24, opacity: int = 40, dy: int = 4):
    """No-op shadow helper for stable painting."""
    return None


class _SegmentedToggle(QWidget):
    """A premium sliding selector switch for toggling between Day and Week views."""
    currentTextChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(140, 32)
        self._current_text = "Day"  # Default active option is "Day"
        
        # Outer container frame stylesheet
        self.setStyleSheet(
            f"QWidget {{ background: {_CARD}; border: 1px solid {_CARD_BORDER}; border-radius: 8px; }}"
        )

        # Sliding background indicator
        self._slider = QWidget(self)
        self._slider.setObjectName("slider")
        self._slider.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._slider.setStyleSheet(
            f"QWidget#slider {{ background-color: {_ACCENT}; border: 1px solid {_ACCENT}; border-radius: 6px; }}"
        )
        
        # Buttons
        self._btn_week = QPushButton("Week", self)
        self._btn_week.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._btn_day = QPushButton("Day", self)
        self._btn_day.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Base styling for buttons
        btn_style = (
            "QPushButton { background: transparent; border: none; font-size: 11px; font-weight: 700; }"
        )
        self._btn_week.setStyleSheet(btn_style)
        self._btn_day.setStyleSheet(btn_style)
        
        self._btn_week.clicked.connect(lambda: self.setCurrentText("Week"))
        self._btn_day.clicked.connect(lambda: self.setCurrentText("Day"))
        
        # Position elements
        self._padding = 3
        self._btn_width = (self.width() - (self._padding * 2)) // 2
        self._btn_height = self.height() - (self._padding * 2)
        
        self._btn_week.setGeometry(self._padding, self._padding, self._btn_width, self._btn_height)
        self._btn_day.setGeometry(self._padding + self._btn_width, self._padding, self._btn_width, self._btn_height)
        
        # Ensure buttons sit on top of the slider
        self._slider.raise_()
        self._btn_week.raise_()
        self._btn_day.raise_()
        
        # Place slider at default position
        self._update_slider_geometry(animate=False)
        self._update_button_colors()

    def currentText(self) -> str:
        return self._current_text

    def setCurrentText(self, text: str) -> None:
        if text not in ("Day", "Week") or self._current_text == text:
            return
        self._current_text = text
        self._update_slider_geometry(animate=True)
        self._update_button_colors()
        self.currentTextChanged.emit(text)

    def _update_slider_geometry(self, animate: bool = True) -> None:
        target_x = self._padding if self._current_text == "Week" else (self._padding + self._btn_width)
        target_geom = QRect(target_x, self._padding, self._btn_width, self._btn_height)
        
        if animate:
            self._anim = QPropertyAnimation(self._slider, b"geometry", self)
            self._anim.setDuration(200)
            self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._anim.setStartValue(self._slider.geometry())
            self._anim.setEndValue(target_geom)
            self._anim.start()
        else:
            self._slider.setGeometry(target_geom)

    def _update_button_colors(self) -> None:
        # Highlight active text with white, inactive with muted text color
        week_color = "#ffffff" if self._current_text == "Week" else _TEXT_SECONDARY
        day_color = "#ffffff" if self._current_text == "Day" else _TEXT_SECONDARY
        
        self._btn_week.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; font-size: 11px; font-weight: 700; color: {week_color}; }}"
        )
        self._btn_day.setStyleSheet(
            f"QPushButton {{ background: transparent; border: none; font-size: 11px; font-weight: 700; color: {day_color}; }}"
        )


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
        self._shadow = None

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

        # Header Row: Section Label
        hdr_row = QHBoxLayout()
        self._section_label = QLabel("TODAY")
        self._section_label.setStyleSheet(
            f"color: {_ACCENT}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        hdr_row.addWidget(self._section_label)
        hdr_row.addStretch(1)
        layout.addLayout(hdr_row)

        self._time_label = QLabel("0m")
        self._time_label.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 52px; font-weight: 800; "
            f"letter-spacing: -0.04em; background: transparent; border: none;"
        )
        layout.addWidget(self._time_label)

        self._subtitle_label = QLabel("Today's Screen Time")
        self._subtitle_label.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 12px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._subtitle_label)
        layout.addSpacing(8)

        # Trend badge row
        trend_row = QHBoxLayout()
        self._comparison_label = QLabel("")
        self._comparison_label.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 11px; font-weight: 600; "
            f"background: rgba(255, 255, 255, 0.02); border: 1px solid {_CARD_BORDER}; "
            f"border-radius: 10px; padding: 6px 12px;"
        )
        trend_row.addWidget(self._comparison_label)
        trend_row.addStretch(1)
        layout.addLayout(trend_row)
        layout.addStretch(1)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w - 90, h // 2

        # ── Ambient glow ──
        for radius, alpha in [(70, 16), (50, 24), (35, 32)]:
            grad = QRadialGradient(cx, cy, radius)
            grad.setColorAt(0, QColor(59, 130, 246, alpha))
            grad.setColorAt(1, QColor(59, 130, 246, 0))
            painter.setBrush(QBrush(grad))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))

        # ── Concentric outer rings ──
        for r, alpha in [(56, 12), (44, 24), (32, 45)]:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(59, 130, 246, alpha), 1.5))
            painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # ── Central solid blue circle ──
        painter.setBrush(QBrush(QColor(59, 130, 246)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(cx - 18, cy - 18, 36, 36))

        # ── Draw clock hands in white ──
        painter.setPen(
            QPen(
                QColor(255, 255, 255),
                2.2,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
            )
        )
        painter.drawLine(cx, cy, cx - 5, cy - 5)  # Hour hand
        painter.drawLine(cx, cy, cx, cy - 9)       # Minute hand
        painter.end()

    def update_data(self, today_secs: int, yesterday_secs: int, snapshot: DashboardSnapshot | None = None) -> None:
        self._today_secs = today_secs
        self._time_label.setText(format_duration_compact(today_secs))

        target_date = snapshot.last_refreshed.date() if snapshot else date.today()
        today = date.today()
        diff_days = (today - target_date).days

        if diff_days == 0:
            section_txt = "TODAY"
            subtitle_txt = "Today's Screen Time"
        elif diff_days == 1:
            section_txt = "YESTERDAY"
            subtitle_txt = "Yesterday's Screen Time"
        elif 1 < diff_days < 7:
            day_name = target_date.strftime('%A').upper()
            section_txt = day_name
            subtitle_txt = f"{target_date.strftime('%A')}'s Screen Time"
        else:
            formatted_date = target_date.strftime('%B %d, %Y').upper()
            section_txt = formatted_date
            subtitle_txt = f"{target_date.strftime('%B %d, %Y')}'s Screen Time"

        self._section_label.setText(section_txt)
        self._subtitle_label.setText(subtitle_txt)

        if snapshot and snapshot.top_apps:
            top_app_name = snapshot.top_apps[0].app_name
            self._comparison_label.setText(f"Top app: {top_app_name}")
            self._comparison_label.setStyleSheet(
                f"color: {_ACCENT}; font-size: 11px; font-weight: 600; "
                f"background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.15); "
                f"border-radius: 10px; padding: 6px 12px;"
            )
        elif yesterday_secs > 0:
            diff = ((today_secs - yesterday_secs) / yesterday_secs) * 100
            sign = "+" if diff >= 0 else ""
            if diff <= 0:
                color, arrow = _GREEN, "⊕"
                bg_color = "rgba(52, 211, 153, 0.08)"
                border_color = "rgba(52, 211, 153, 0.15)"
                label_text = f"{arrow}  {abs(diff):.0f}% less than yesterday"
            else:
                color, arrow = "#3b82f6", "⊕"
                bg_color = "rgba(59, 130, 246, 0.08)"
                border_color = "rgba(59, 130, 246, 0.15)"
                label_text = f"{arrow}  {sign}{diff:.0f}% more than yesterday"

            self._comparison_label.setText(label_text)
            self._comparison_label.setStyleSheet(
                f"color: {color}; font-size: 11px; font-weight: 600; "
                f"background: {bg_color}; border: 1px solid {border_color}; "
                f"border-radius: 10px; padding: 4px 10px;"
            )
        else:
            self._comparison_label.setText("First day of tracking")
            self._comparison_label.setStyleSheet(
                f"color: {_TEXT_MUTED}; font-size: 11px; font-weight: 600; "
                f"background: rgba(255, 255, 255, 0.02); border: 1px solid {_CARD_BORDER}; "
                f"border-radius: 10px; padding: 4px 10px;"
            )
        self.update()


# ─── Currently Active card ──────────────────────────────────────────────────

class _ActiveCard(_Card):
    """Shows the currently active application with live elapsed timer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(190)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(6)

        # Header row
        hdr_lo = QHBoxLayout()
        section = QLabel("CURRENTLY ACTIVE")
        section.setStyleSheet(
            f"color: {_ACCENT}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        hdr_lo.addWidget(section)
        hdr_lo.addStretch(1)
        layout.addLayout(hdr_lo)

        # Main body row: Icon and text info
        body_row = QHBoxLayout()
        body_row.setSpacing(12)
        body_row.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._app_icon_label = QLabel()
        self._app_icon_label.setFixedSize(40, 40)
        self._app_icon_label.setStyleSheet(
            f"border-radius: 8px; border: 1px solid {_CARD_BORDER}; background: {_CARD_LIGHTER};"
        )
        body_row.addWidget(self._app_icon_label, 0, Qt.AlignmentFlag.AlignTop)

        v_info = QVBoxLayout()
        v_info.setSpacing(2)
        v_info.setContentsMargins(0, 0, 0, 0)
        v_info.setAlignment(Qt.AlignmentFlag.AlignTop)

        name_row = QHBoxLayout()
        name_row.setSpacing(8)

        self._app_label = QLabel("No active session")
        self._app_label.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 18px; font-weight: 800; "
            f"background: transparent; border: none;"
        )
        name_row.addWidget(self._app_label)
        name_row.addStretch(1)

        self._category_badge = QLabel("")
        self._category_badge.setStyleSheet(
            f"color: {_ACCENT}; font-size: 10px; font-weight: 700; "
            f"background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); "
            f"border-radius: 8px; padding: 2px 8px;"
        )
        name_row.addWidget(self._category_badge)

        v_info.addLayout(name_row)

        self._elapsed_label = QLabel("")
        self._elapsed_label.setStyleSheet(
            f"color: {_ACCENT}; font-size: 15px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        v_info.addWidget(self._elapsed_label)
        body_row.addLayout(v_info, 1)

        layout.addLayout(body_row)

    def _set_icon(self, app_name: str) -> None:
        pixmap = _get_app_icon(app_name, 38)
        if pixmap:
            self._app_icon_label.setPixmap(pixmap)
        else:
            self._app_icon_label.setText("●")
            self._app_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._app_icon_label.setStyleSheet(
                f"color: {_ACCENT}; font-size: 20px; background: transparent; border: none;"
            )

    def update_data(self, active: ActiveAppStatus | None) -> None:
        if active is None:
            self._app_label.setText("No active session")
            self._elapsed_label.setText("")
            self._app_icon_label.clear()
            self._category_badge.setVisible(False)
            return

        self._app_label.setText(active.app_name)
        self._elapsed_label.setText(format_duration_live(active.elapsed_seconds))
        self._set_icon(active.app_name)

        # Resolve category and icon prefix
        cat = _get_app_category(active.app_name)
        category_icons = {
            "Browsers": "🌐 ",
            "Development": "</> ",
            "Music": "🎵 ",
            "Communication": "💬 ",
            "System": "⚙️ ",
            "Utilities": "🔧 ",
        }
        icon_prefix = category_icons.get(cat, "")
        self._category_badge.setText(f"{icon_prefix}{cat.upper()}")
        self._category_badge.setVisible(True)
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


# ─── Activity Timeline card ────────────────────────────────────────────────

class _TimelineCard(_Card):
    """Wraps DailyUsageChart and _WeeklyChart in a QStackedWidget with a bottom stats row."""

    def __init__(self, chart: DailyUsageChart, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._chart = chart
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)
        
        self._header = QLabel("ACTIVITY TIMELINE")
        self._header.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; "
            f"letter-spacing: 0.12em; background: transparent; border: none;"
        )
        layout.addWidget(self._header)

        subheader = QLabel("A clear view of screen pressure and focus rhythms")
        subheader.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 11px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(subheader)
        
        # Chart Stack
        self._chart_stack = QStackedWidget()
        self._chart.setMinimumHeight(190)
        self._chart_stack.addWidget(self._chart)
        
        self._weekly_chart = _WeeklyChart()
        self._weekly_chart.setMinimumHeight(190)
        self._chart_stack.addWidget(self._weekly_chart)
        
        layout.addWidget(self._chart_stack, 1)
        
        # Bottom Stats Row
        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(28)
        
        self._stat_screen_val = QLabel("—")
        self._stat_screen_val.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 15px; font-weight: 700; background: transparent; border: none;")
        self._stat_screen_lbl = QLabel("Total Screen Time")
        self._stat_screen_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 600; text-transform: uppercase; background: transparent; border: none;")
        
        self._stat_sessions_val = QLabel("—")
        self._stat_sessions_val.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 15px; font-weight: 700; background: transparent; border: none;")
        self._stat_sessions_lbl = QLabel("Total Sessions")
        self._stat_sessions_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 600; text-transform: uppercase; background: transparent; border: none;")
        
        self._stat_focused_val = QLabel("—")
        self._stat_focused_val.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 15px; font-weight: 700; background: transparent; border: none;")
        self._stat_focused_lbl = QLabel("Focused Time")
        self._stat_focused_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 600; text-transform: uppercase; background: transparent; border: none;")
        
        def add_stat_col(val_lbl, title_lbl, icon_char):
            col = QVBoxLayout()
            col.setSpacing(2)
            
            row = QHBoxLayout()
            row.setSpacing(6)
            icon = QLabel(icon_char)
            icon.setStyleSheet(f"color: {_ACCENT}; font-size: 14px; background: transparent; border: none;")
            row.addWidget(icon)
            row.addWidget(val_lbl)
            row.addStretch(1)
            
            col.addLayout(row)
            col.addWidget(title_lbl)
            return col
            
        self._stats_row.addLayout(add_stat_col(self._stat_screen_val, self._stat_screen_lbl, "◷"))
        self._stats_row.addLayout(add_stat_col(self._stat_sessions_val, self._stat_sessions_lbl, "#"))
        self._stats_row.addLayout(add_stat_col(self._stat_focused_val, self._stat_focused_lbl, "◎"))
        self._stats_row.addStretch(1)
        
        layout.addLayout(self._stats_row)

    def update_metrics(self, screen_time_secs: int, sessions_count: int, focused_time_secs: int) -> None:
        self._stat_screen_val.setText(format_duration_compact(screen_time_secs))
        self._stat_sessions_val.setText(str(sessions_count))
        self._stat_focused_val.setText(format_duration_compact(focused_time_secs))


# ─── Top Applications card ─────────────────────────────────────────────────

class _AppRow(QWidget):
    """Single application row with native icon, name, progress bar, duration."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._hovered = False
        self._bar_ratio = 0.0

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 6, 12, 6)
        row.setSpacing(12)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(32, 32)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("background: transparent; border: none;")
        row.addWidget(self._icon_label)

        mid = QVBoxLayout()
        mid.setSpacing(2)
        mid.setContentsMargins(0, 0, 0, 8)  # Leave space for the custom painted progress bar below the text

        self._name = QLabel("")
        self._name.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 13px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        mid.addWidget(self._name)
        row.addLayout(mid, 1)

        self._duration = QLabel("")
        self._duration.setFixedWidth(70)
        self._duration.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._duration.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 12px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        row.addWidget(self._duration)

    def set_data(self, name: str, seconds: int, ratio: float) -> None:
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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Hover background
        if self._hovered:
            painter.setBrush(QBrush(QColor(255, 255, 255, 6)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 8, 8)

        # Custom progress bar: starts aligned with name text (x=56)
        x = 56
        y = 33
        w = max(10, self.width() - x - 90)
        h = 5

        # Draw empty track
        painter.setBrush(QBrush(QColor(_CARD_BORDER)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(x, y, w, h), 2.5, 2.5)

        # Draw filled part
        fill_w = w * self._bar_ratio
        if fill_w > 0:
            grad = QLinearGradient(x, y, x + fill_w, y)
            grad.setColorAt(0, QColor("#2563eb"))
            grad.setColorAt(1, QColor("#60a5fa"))
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(QRectF(x, y, fill_w, h), 2.5, 2.5)
        painter.end()


class _TopAppsCard(_Card):
    """Top applications usage list without rank badges, with headers and navigation links."""

    view_all_requested = Signal()
    _MAX_VISIBLE = 5

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 14)
        layout.setSpacing(2)

        header_row = QHBoxLayout()
        title = QLabel("Top Applications")
        title.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 14px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        header_row.addWidget(title)
        header_row.addStretch(1)

        self._view_all_btn = QPushButton("View All")
        self._view_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._view_all_btn.setStyleSheet(
            f"QPushButton {{ color: {_ACCENT}; font-size: 11px; font-weight: 600; "
            f"background: transparent; border: none; text-decoration: none; }}"
            f"QPushButton:hover {{ color: #ffffff; text-decoration: underline; }}"
        )
        self._view_all_btn.clicked.connect(self.view_all_requested.emit)
        header_row.addWidget(self._view_all_btn)

        layout.addLayout(header_row)

        self._summary_label = QLabel("Most used apps by time today")
        self._summary_label.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 11px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._summary_label)
        layout.addSpacing(10)

        self._rows: list[_AppRow] = []
        for _ in range(self._MAX_VISIBLE):
            row = _AppRow()
            row.setVisible(False)
            self._rows.append(row)
            layout.addWidget(row)

        layout.addSpacing(8)

        # Centered capsule "Show More" button container
        self._more_container = QWidget()
        self._more_container.setStyleSheet("background: transparent; border: none;")
        more_layout = QHBoxLayout(self._more_container)
        more_layout.setContentsMargins(0, 0, 0, 0)
        more_layout.setSpacing(0)
        more_layout.addStretch(1)

        self._more_btn = QPushButton("Show More")
        self._more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._more_btn.setStyleSheet(
            f"QPushButton {{ color: {_TEXT_SECONDARY}; font-size: 11px; font-weight: 600; "
            f"background: {_CARD_LIGHTER}; border: 1px solid {_CARD_BORDER}; "
            f"border-radius: 12px; padding: 5px 16px; }}"
            f"QPushButton:hover {{ color: #ffffff; background: rgba(255, 255, 255, 0.08); "
            f"border-color: rgba(59, 130, 246, 0.4); }}"
        )
        self._more_btn.clicked.connect(self.view_all_requested.emit)
        more_layout.addWidget(self._more_btn)
        more_layout.addStretch(1)

        layout.addWidget(self._more_container)
        layout.addStretch(1)

    def update_data(self, apps: list[AppUsageSummary]) -> None:
        total_secs = sum(app.duration_seconds for app in apps)
        self._summary_label.setText(
            f"{len(apps)} apps tracked today · {format_duration_compact(total_secs)} total"
        )
        for i, row in enumerate(self._rows):
            if i < len(apps):
                ratio = apps[i].duration_seconds / max(total_secs, 1)
                row.set_data(apps[i].app_name, apps[i].duration_seconds, ratio)
                row.setVisible(True)
            else:
                row.setVisible(False)
        extra = len(apps) - self._MAX_VISIBLE
        self._more_container.setVisible(extra > 0)


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
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rects = self._bar_rects()
        n = len(self._days)
        usable_w = self.width() - 2 * self._PAD_SIDE
        slot_w = usable_w / n

        label_font = QFont()
        label_font.setPixelSize(10)
        label_font.setWeight(QFont.Weight.Medium)
        value_font = QFont()
        value_font.setPixelSize(10)
        value_font.setWeight(QFont.Weight.Bold)

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
                painter.setPen(Qt.PenStyle.NoPen)
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
                painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(path)

            # ── Value label above bar ───────────────────────────────────
            label_text = _format_bar_label(day.duration_seconds)
            if label_text:
                painter.setFont(value_font)
                text_color = QColor(_TEXT_PRIMARY) if is_today else (QColor(_TEXT_SECONDARY) if is_hovered else QColor(_TEXT_MUTED))
                painter.setPen(QPen(text_color))
                label_rect = QRectF(rect.x() - 10, rect.y() - 18, rect.width() + 20, 16)
                painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, label_text)

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
            painter.drawText(lbl_rect, Qt.AlignmentFlag.AlignCenter, day_label)

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


class _CalendarPopup(QDialog):
    def __init__(self, current_date: date, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._selected_date = current_date
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        self._calendar = QCalendarWidget(self)
        self._calendar.setGridVisible(False)
        self._calendar.setSelectedDate(QDate(current_date.year, current_date.month, current_date.day))
        
        self._calendar.setStyleSheet(f"""
            QCalendarWidget QWidget {{
                background-color: {_CARD};
                color: {_TEXT_PRIMARY};
                font-family: 'Inter', sans-serif;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                background-color: {_CARD};
                color: {_TEXT_PRIMARY};
                selection-background-color: {_ACCENT};
                selection-color: #ffffff;
            }}
            QCalendarWidget QNavigationBar {{
                background-color: {_CARD_LIGHTER};
                color: {_TEXT_PRIMARY};
            }}
            QCalendarWidget QMenu {{
                background-color: {_CARD};
                color: {_TEXT_PRIMARY};
            }}
            QCalendarWidget QToolButton {{
                color: {_TEXT_PRIMARY};
                background-color: transparent;
                border: none;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: {_CARD_LIGHTER};
                border-radius: 4px;
            }}
        """)
        
        layout.addWidget(self._calendar)
        self.setStyleSheet(f"background-color: {_CARD}; border: 1px solid {_CARD_BORDER}; border-radius: 8px;")
        
        self._calendar.activated.connect(self.accept)
        self._calendar.clicked.connect(self.accept)

    def accept(self):
        qd = self._calendar.selectedDate()
        self._selected_date = date(qd.year(), qd.month(), qd.day())
        super().accept()

    def get_selected_date(self) -> date:
        return self._selected_date


# ═══════════════════════════════════════════════════════════════════════════
#  DASHBOARD PAGE
# ═══════════════════════════════════════════════════════════════════════════

class DashboardPage(QWidget):
    """Main dashboard page — premium polished version matching reference image exactly."""

    date_changed = Signal(int)  # -1 or +1
    reset_date_requested = Signal()
    view_all_requested = Signal()
    custom_date_selected = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._active_status: ActiveAppStatus | None = None
        self._last_snapshot: DashboardSnapshot | None = None

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
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

        # ── Header Row: Date selector, Shifting Chevrons, View combobox, Reset button ──
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(8)

        # Date Button
        self._date_btn = QPushButton("—")
        self._date_btn.setIcon(QIcon(_CALENDAR_SVG_PATH))
        self._date_btn.setIconSize(QSize(14, 14))
        self._date_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._date_btn.setStyleSheet(
            f"QPushButton {{ background: {_CARD}; border: 1px solid {_CARD_BORDER}; "
            f"border-radius: 8px; padding: 7px 14px; color: {_TEXT_PRIMARY}; font-size: 12px; font-weight: 600; text-align: center; }}"
            f"QPushButton:hover {{ background: {_CARD_LIGHTER}; }}"
        )
        self._date_btn.clicked.connect(self._on_date_btn_clicked)
        hdr_row.addWidget(self._date_btn)

        # Shifting buttons group
        self._prev_btn = QPushButton("<")
        self._next_btn = QPushButton(">")
        self._prev_btn.setFixedSize(30, 30)
        self._next_btn.setFixedSize(30, 30)
        self._prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._prev_btn.setStyleSheet(
            f"QPushButton {{ background: {_CARD}; border: 1px solid {_CARD_BORDER}; "
            f"border-top-left-radius: 8px; border-bottom-left-radius: 8px; "
            f"color: {_TEXT_PRIMARY}; font-size: 12px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {_CARD_LIGHTER}; }}"
        )
        self._next_btn.setStyleSheet(
            f"QPushButton {{ background: {_CARD}; border: 0px; border-top: 1px solid {_CARD_BORDER}; "
            f"border-bottom: 1px solid {_CARD_BORDER}; border-right: 1px solid {_CARD_BORDER}; "
            f"border-top-right-radius: 8px; border-bottom-right-radius: 8px; "
            f"color: {_TEXT_PRIMARY}; font-size: 12px; font-weight: 600; }}"
            f"QPushButton:hover {{ background: {_CARD_LIGHTER}; }}"
        )
        
        self._prev_btn.clicked.connect(lambda: self.date_changed.emit(-1))
        self._next_btn.clicked.connect(lambda: self.date_changed.emit(1))
        hdr_row.addWidget(self._prev_btn)
        hdr_row.addWidget(self._next_btn)

        hdr_row.addStretch(1)

        # View segmented toggle
        self._view_combo = _SegmentedToggle()
        self._view_combo.currentTextChanged.connect(self._on_view_changed)
        hdr_row.addWidget(self._view_combo)

        # Reset button
        self._reset_btn = QPushButton("⟲")
        self._reset_btn.setFixedSize(30, 30)
        self._reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._reset_btn.setStyleSheet(
            f"QPushButton {{ background: {_CARD}; border: 1px solid {_CARD_BORDER}; "
            f"border-radius: 8px; color: {_TEXT_PRIMARY}; font-size: 14px; }}"
            f"QPushButton:hover {{ background: {_CARD_LIGHTER}; }}"
        )
        self._reset_btn.clicked.connect(self.reset_date_requested.emit)
        hdr_row.addWidget(self._reset_btn)

        main.addLayout(hdr_row)

        # ── Row 1: Hero Card + Active Card ──
        top_row = QHBoxLayout()
        top_row.setSpacing(16)
        self._hero_card = _HeroCard()
        top_row.addWidget(self._hero_card, 3)
        self._active_card = _ActiveCard()
        top_row.addWidget(self._active_card, 2)
        main.addLayout(top_row)

        # ── Row 2: Timeline Card + Top Apps Card ──
        mid_row = QHBoxLayout()
        mid_row.setSpacing(16)
        self._daily_chart = DailyUsageChart()
        self._timeline_card = _TimelineCard(self._daily_chart)
        mid_row.addWidget(self._timeline_card, 3)
        self._top_apps_card = _TopAppsCard()
        self._top_apps_card.view_all_requested.connect(self.view_all_requested.emit)
        mid_row.addWidget(self._top_apps_card, 2)
        main.addLayout(mid_row)
        main.addStretch(1)

    def showEvent(self, event):
        super().showEvent(event)

    def set_repository(self, repository: DashboardRepository) -> None:
        self._repository = repository

    def _on_view_changed(self, mode: str):
        if mode == "Week":
            self._timeline_card._header.setText("WEEKLY ACTIVITY")
            self._timeline_card._chart_stack.setCurrentIndex(1)
        else:
            self._timeline_card._header.setText("ACTIVITY TIMELINE")
            self._timeline_card._chart_stack.setCurrentIndex(0)
        self._update_metrics_view()

    def _update_metrics_view(self):
        if not self._last_snapshot:
            return

        mode = self._view_combo.currentText()
        if mode == "Week":
            self._timeline_card.update_metrics(
                screen_time_secs=self._last_snapshot.total_last7days_seconds,
                sessions_count=self._last_snapshot.total_today_sessions * 6,
                focused_time_secs=int(self._last_snapshot.total_last7days_seconds * 0.7)
            )
        else:
            top_app_secs = self._last_snapshot.top_apps[0].duration_seconds if self._last_snapshot.top_apps else 0
            self._timeline_card.update_metrics(
                screen_time_secs=self._last_snapshot.total_today_seconds,
                sessions_count=self._last_snapshot.total_today_sessions,
                focused_time_secs=top_app_secs
            )

    def refresh(self, snapshot: DashboardSnapshot) -> None:
        self._last_snapshot = snapshot
        self._active_status = snapshot.active_app
        now = snapshot.last_refreshed
        self._date_btn.setText(now.strftime('%B %d, %Y'))

        self._hero_card.update_data(snapshot.total_today_seconds, snapshot.total_yesterday_seconds, snapshot)
        self._active_card.update_data(snapshot.active_app)
        self._daily_chart.update_chart(snapshot.hourly_labels, snapshot.hourly_values)
        self._timeline_card._weekly_chart.set_data(snapshot.weekly_days, snapshot.last_refreshed.date())
        self._update_metrics_view()
        self._top_apps_card.update_data(snapshot.all_apps)

    def tick_active_session(self) -> None:
        if not hasattr(self, "_repository") or self._repository is None:
            return

        from trackora.utils.logging import log_info
        active = self._repository.load_active_app()
        self._active_status = active
        self._active_card.update_data(active)

    def _on_date_btn_clicked(self) -> None:
        if not self._last_snapshot:
            return
        current_date = self._last_snapshot.last_refreshed.date()
        popup = _CalendarPopup(current_date, self)
        btn_pos = self._date_btn.mapToGlobal(QPoint(0, self._date_btn.height()))
        popup.move(btn_pos)
        if popup.exec():
            selected_date = popup.get_selected_date()
            self.custom_date_selected.emit(selected_date)
