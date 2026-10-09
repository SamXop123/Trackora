"""Calendar page — monthly screen-time overview for Trackora.

Answers: "How did I spend my time across the month?"
Features:
- Clean 7-column monthly calendar (Mon → Sun).
- Fixed pixel-perfect column header and day cell alignment.
- Rock-solid layout structure with zero shifting, jumping, or clipping.
- In-place reusable day cell widgets (zero widget destruction during navigation).
- Subtle usage intensity tiers matching Trackora's navy/accent visual language.
- Lightweight 120ms hover animations via QPainter without stylesheet churn.
- Compact Day Details side panel showing key metrics, category breakdown, and major app usage.
- Smooth month navigation and jump-to-today action.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QRect,
    QRectF,
    QSize,
    Qt,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from trackora.gui.ui_common import recycle_widgets_in_place
from trackora.gui.utils import get_app_icon
from trackora.models.dashboard import AppUsageSummary, ReportsData
from trackora.utils.formatting import format_duration_compact

if TYPE_CHECKING:
    from trackora.database.dashboard import DashboardRepository

# ── Color tokens matching Trackora's visual identity ─────────────────────────
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

# ── Category SVGs for productive/category breakdown ──────────────────────────
_CATEGORY_SVGS: dict[str, str] = {
    "Browsers": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="10"></circle>
  <line x1="2" y1="12" x2="22" y2="12"></line>
  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
</svg>""",
    "Development": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <polyline points="16 18 22 12 16 6"></polyline>
  <polyline points="8 6 2 12 8 18"></polyline>
</svg>""",
    "Music": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M9 18V5l12-2v13"></path>
  <circle cx="6" cy="18" r="3"></circle>
  <circle cx="18" cy="16" r="3"></circle>
</svg>""",
    "Communication": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
</svg>""",
    "Utilities": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
</svg>""",
    "System": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="3"></circle>
  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
</svg>""",
    "Other": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
  <line x1="16.5" y1="9.4" x2="7.5" y2="4.21"></line>
  <polygon points="12 22.08 12 12 3 6.92 3 17.08 12 22.08"></polygon>
  <polygon points="12 12 21 6.92 21 17.08 12 22.08"></polygon>
  <polygon points="12 2 21 6.92 12 12 3 6.92 12 2"></polygon>
  <line x1="12" y1="22.08" x2="12" y2="12"></line>
</svg>""",
}


def _get_category_pixmap(cat: str, size: int, color_hex: str) -> QPixmap:
    from PySide6.QtCore import QByteArray

    svg_text = _CATEGORY_SVGS.get(cat, _CATEGORY_SVGS["Other"])
    svg_text = svg_text.replace('stroke="currentColor"', f'stroke="{color_hex}"')
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer = QSvgRenderer(QByteArray(svg_text.encode("utf-8")))
    renderer.render(painter)
    painter.end()
    return pixmap


def _blend_colors(c1: QColor, c2: QColor, factor: float) -> QColor:
    f = max(0.0, min(1.0, factor))
    r = int(c1.red() + (c2.red() - c1.red()) * f)
    g = int(c1.green() + (c2.green() - c1.green()) * f)
    b = int(c1.blue() + (c2.blue() - c1.blue()) * f)
    a = int(c1.alpha() + (c2.alpha() - c1.alpha()) * f)
    return QColor(r, g, b, a)


# ═════════════════════════════════════════════════════════════════════════════
#  BASE CARD
# ═════════════════════════════════════════════════════════════════════════════


class _Card(QFrame):
    """Reusable base card container with clean dark background and border."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("calendarCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(
            f"QFrame#calendarCard {{ background: {_CARD}; border: 1px solid {_CARD_BORDER}; border-radius: 14px; }}"
        )


# ═════════════════════════════════════════════════════════════════════════════
#  NAVIGATION BUTTON
# ═════════════════════════════════════════════════════════════════════════════


class _NavIconBtn(QWidget):
    """Subtle, animated navigation button for month switching and jumping to today."""

    clicked = Signal()

    def __init__(
        self,
        text: str,
        tooltip: str = "",
        fixed_width: int = 34,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._text = text
        self._hover_val = 0.0
        self.setFixedHeight(32)
        if fixed_width > 0:
            self.setFixedWidth(fixed_width)
        else:
            self.setMinimumWidth(58)
        if tooltip:
            self.setToolTip(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._anim = QVariantAnimation(self)
        self._anim.setDuration(120)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.valueChanged.connect(self._on_anim)

    def _on_anim(self, val: float) -> None:
        self._hover_val = float(val)
        self.update()

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self._anim.stop()
        self._anim.setStartValue(self._hover_val)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self._anim.stop()
        self._anim.setStartValue(self._hover_val)
        self._anim.setEndValue(0.0)
        self._anim.start()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        bg = _blend_colors(QColor(_CARD_LIGHTER), QColor(28, 42, 64), self._hover_val)
        border = _blend_colors(QColor(_CARD_BORDER), QColor(_ACCENT), self._hover_val)
        text_color = _blend_colors(QColor(_TEXT_SECONDARY), QColor(_TEXT_PRIMARY), self._hover_val)

        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(border, 1.0))
        painter.drawRoundedRect(rect, 8.0, 8.0)

        font = self.font()
        font.setFamily("Inter")
        font.setPointSizeF(10.0)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(text_color))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._text)
        painter.end()


# ═════════════════════════════════════════════════════════════════════════════
#  CALENDAR DAY CELL
# ═════════════════════════════════════════════════════════════════════════════


class _CalendarDayCell(QWidget):
    """A compact, high-fidelity day cell in the 7-column calendar.

    Usage Intensity Tiers (Subtle & Premium, not an aggressive heatmap):
    - Tier 0: 0 seconds (no activity, clean dark card)
    - Tier 1: > 0 to < 1.5h (very low usage: subtle navy tint, soft indicator)
    - Tier 2: 1.5h to 5h (normal usage: medium navy presence, accent pill)
    - Tier 3: > 5h (high usage / deep focus: rich deep navy, bright accent pill)
    """

    clicked = Signal(date)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._date: date | None = None
        self._in_current_month: bool = True
        self._is_today: bool = False
        self._is_selected: bool = False
        self._duration_seconds: int = 0

        self.setMinimumSize(QSize(54, 62))
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Smooth 120ms hover animation
        self._hover_val = 0.0
        self._hover_anim = QVariantAnimation(self)
        self._hover_anim.setDuration(120)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._hover_anim.setStartValue(0.0)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.valueChanged.connect(self._on_hover_step)

    def _on_hover_step(self, val: float) -> None:
        self._hover_val = float(val)
        self.update()

    def set_day_data(
        self,
        d: date,
        in_month: bool,
        is_today: bool,
        is_selected: bool,
        duration_seconds: int,
    ) -> None:
        """In-place data update avoiding widget destruction."""
        self._date = d
        self._in_current_month = in_month
        self._is_today = is_today
        self._is_selected = is_selected
        self._duration_seconds = max(0, duration_seconds)
        self.update()

    def set_selected(self, selected: bool) -> None:
        if self._is_selected != selected:
            self._is_selected = selected
            self.update()

    def enterEvent(self, event) -> None:
        super().enterEvent(event)
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_val)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()

    def leaveEvent(self, event) -> None:
        super().leaveEvent(event)
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_val)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._date is not None:
            self.clicked.emit(self._date)

    def paintEvent(self, event) -> None:
        if self._date is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = float(self.width())
        h = float(self.height())
        rect = QRectF(0.5, 0.5, w - 1.0, h - 1.0)

        # 1. Determine Usage Tier
        secs = self._duration_seconds
        if secs <= 0:
            tier = 0
        elif secs < 5400:  # < 1.5h
            tier = 1
        elif secs < 18000:  # 1.5h - 5h
            tier = 2
        else:  # >= 5h
            tier = 3

        # 2. Base Background & Border
        if not self._in_current_month:
            # Clean dark container for days outside current month
            base_bg = QColor("#0f141f")
            base_border = QColor("#192230")
        else:
            if tier == 0:
                base_bg = QColor(_CARD)  # #141a23
                base_border = QColor(_CARD_BORDER)  # #1c2735
            elif tier == 1:
                base_bg = QColor(19, 28, 42)
                base_border = QColor(28, 44, 68)
            elif tier == 2:
                base_bg = QColor(22, 34, 52)
                base_border = QColor(33, 56, 86)
            else:
                base_bg = QColor(26, 42, 68)
                base_border = QColor(42, 72, 110)

        # 3. Hover Blend
        hover_bg_target = QColor(27, 40, 60)
        hover_border_target = QColor(59, 130, 246)

        current_bg = _blend_colors(base_bg, hover_bg_target, self._hover_val * 0.7)
        current_border = _blend_colors(base_border, hover_border_target, self._hover_val * 0.9)

        # 4. Selection Highlight
        if self._is_selected:
            current_border = QColor(_ACCENT)
            current_bg = _blend_colors(current_bg, QColor(29, 48, 76), 0.7)

        # Draw Cell Background
        painter.setBrush(QBrush(current_bg))
        pen_width = 1.6 if self._is_selected else 1.0
        painter.setPen(QPen(current_border, pen_width))
        painter.drawRoundedRect(rect, 8.0, 8.0)

        # 5. Top Row: Day Number + Today Highlight
        day_num_str = str(self._date.day)

        if self._is_today:
            # Restrained accent pill for today
            today_pill_size = 20.0
            pill_rect = QRectF(6.0, 6.0, today_pill_size, today_pill_size)
            painter.setBrush(QBrush(QColor(_ACCENT)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(pill_rect, 5.0, 5.0)

            font_day = QFont("Inter")
            font_day.setPointSizeF(9.5)
            font_day.setBold(True)
            painter.setFont(font_day)
            painter.setPen(QPen(QColor("#ffffff")))
            painter.drawText(pill_rect, Qt.AlignmentFlag.AlignCenter, day_num_str)
        else:
            font_day = QFont("Inter")
            font_day.setPointSizeF(9.5)
            font_day.setBold(self._in_current_month and (tier > 0 or self._is_selected))
            painter.setFont(font_day)

            if not self._in_current_month:
                painter.setPen(QPen(QColor(_TEXT_MUTED)))
            else:
                painter.setPen(QPen(QColor(_TEXT_PRIMARY)))

            day_text_rect = QRectF(8.0, 7.0, 26.0, 18.0)
            painter.drawText(day_text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, day_num_str)

        # 6. Usage Intensity Pill in upper-right
        if self._in_current_month and tier > 0:
            if tier == 1:
                pill_color = QColor(59, 130, 246, 120)
                pill_w = 10.0
            elif tier == 2:
                pill_color = QColor(59, 130, 246, 200)
                pill_w = 14.0
            else:
                pill_color = QColor(96, 165, 250, 255)
                pill_w = 18.0

            indicator_rect = QRectF(w - pill_w - 7.0, 9.0, pill_w, 3.5)
            painter.setBrush(QBrush(pill_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(indicator_rect, 1.75, 1.75)

        # 7. Bottom Row: Duration String
        font_dur = QFont("Inter")
        font_dur.setPointSizeF(8.5)

        if self._in_current_month:
            if tier > 0:
                dur_str = format_duration_compact(secs)
                if tier == 3:
                    dur_color = QColor("#93c5fd")
                    font_dur.setBold(True)
                elif tier == 2:
                    dur_color = QColor(_TEXT_PRIMARY)
                    font_dur.setBold(True)
                else:
                    dur_color = QColor(_TEXT_SECONDARY)
                    font_dur.setBold(False)
            else:
                dur_str = "—"
                dur_color = QColor("#3a4b60")
                font_dur.setBold(False)

            painter.setFont(font_dur)
            painter.setPen(QPen(dur_color))
            dur_rect = QRectF(8.0, h - 21.0, w - 16.0, 15.0)
            painter.drawText(dur_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, dur_str)
        else:
            if secs > 0:
                dur_str = format_duration_compact(secs)
                painter.setFont(font_dur)
                painter.setPen(QPen(QColor(86, 106, 130, 140)))
                dur_rect = QRectF(8.0, h - 21.0, w - 16.0, 15.0)
                painter.drawText(dur_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, dur_str)

        painter.end()


# ═════════════════════════════════════════════════════════════════════════════
#  CALENDAR MONTH SURFACE (7 COLUMNS)
# ═════════════════════════════════════════════════════════════════════════════


class _CalendarMonthSurface(_Card):
    """Container holding the 7-column header and 42 persistent day cells in a single aligned grid."""

    day_selected = Signal(date)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._year: int = date.today().year
        self._month: int = date.today().month
        self._selected_date: date = date.today()
        self._cells: list[_CalendarDayCell] = []

        self.setMinimumHeight(490)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        # Single unified QGridLayout for 100% pixel-perfect column alignment
        self._grid_layout = QGridLayout()
        self._grid_layout.setContentsMargins(0, 0, 0, 0)
        self._grid_layout.setHorizontalSpacing(8)
        self._grid_layout.setVerticalSpacing(8)

        # Row 0: Column headers (MON → SUN)
        weekday_names = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        for col, name in enumerate(weekday_names):
            lbl = QLabel(name)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedHeight(22)
            lbl.setStyleSheet(
                f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; "
                f"letter-spacing: 0.1em; background: transparent; border: none;"
            )
            self._grid_layout.addWidget(lbl, 0, col)

        # Rows 1 to 6: 42 Persistent Day Cells
        for r in range(6):
            for c in range(7):
                cell = _CalendarDayCell()
                cell.clicked.connect(self._on_cell_clicked)
                self._grid_layout.addWidget(cell, r + 1, c)
                self._cells.append(cell)

        layout.addLayout(self._grid_layout, 1)

    def _on_cell_clicked(self, d: date) -> None:
        self.set_selected_date(d)
        self.day_selected.emit(d)

    def set_selected_date(self, d: date) -> None:
        """Update selection across cells without recreating anything."""
        self._selected_date = d
        for cell in self._cells:
            cell.set_selected(cell._date == d)

    def update_grid(
        self,
        year: int,
        month: int,
        usage_map: dict[date, int],
        selected_date: date,
    ) -> None:
        """Populate the 42 cells in-place for the given month."""
        self._year = year
        self._month = month
        self._selected_date = selected_date

        first_of_month = date(year, month, 1)
        start_day_offset = first_of_month.weekday()  # Mon = 0, Sun = 6
        grid_start = first_of_month - timedelta(days=start_day_offset)
        today = date.today()

        for i, cell in enumerate(self._cells):
            cur_date = grid_start + timedelta(days=i)
            in_month = (cur_date.year == year and cur_date.month == month)
            is_today = (cur_date == today)
            is_selected = (cur_date == selected_date)
            dur = usage_map.get(cur_date, 0)
            cell.set_day_data(cur_date, in_month, is_today, is_selected, dur)


