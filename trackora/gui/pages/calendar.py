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


# ═════════════════════════════════════════════════════════════════════════════
#  DAY DETAILS PANEL (Secondary, informative, non-intrusive)
# ═════════════════════════════════════════════════════════════════════════════


class _AppUsageRow(QWidget):
    """Compact application row inside the Day Details panel."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(34)
        self.setStyleSheet("background: transparent;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(10)

        self._icon_lbl = QLabel()
        self._icon_lbl.setFixedSize(18, 18)
        self._icon_lbl.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._icon_lbl)

        name_dur_col = QVBoxLayout()
        name_dur_col.setContentsMargins(0, 0, 0, 0)
        name_dur_col.setSpacing(2)

        self._name_lbl = QLabel("—")
        self._name_lbl.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 12px; font-weight: 600; background: transparent; border: none;"
        )
        name_dur_col.addWidget(self._name_lbl)

        self._bar_bg = QFrame()
        self._bar_bg.setFixedHeight(3)
        self._bar_bg.setStyleSheet(f"background: #1c2735; border-radius: 1px;")
        name_dur_col.addWidget(self._bar_bg)

        layout.addLayout(name_dur_col, 1)

        self._dur_lbl = QLabel("0m")
        self._dur_lbl.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 11px; font-weight: 500; background: transparent; border: none;"
        )
        layout.addWidget(self._dur_lbl)

    def set_app_data(self, app_name: str, duration_sec: int, max_sec: int) -> None:
        self._name_lbl.setText(app_name)
        self._dur_lbl.setText(format_duration_compact(duration_sec))

        pixmap = get_app_icon(app_name, 18, on_loaded=self._on_icon_loaded)
        if pixmap and not pixmap.isNull():
            self._icon_lbl.setPixmap(pixmap)
        else:
            self._icon_lbl.clear()

        pct = max(3, int((duration_sec / max(1, max_sec)) * 100))
        self._bar_bg.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, "
            f"stop:0 {_ACCENT}, stop:{pct/100:.2f} {_ACCENT}, stop:{(pct+0.01)/100:.2f} #1c2735, stop:1 #1c2735); "
            f"border-radius: 1px;"
        )

    def _on_icon_loaded(self, pixmap: QPixmap | None) -> None:
        if pixmap and not pixmap.isNull():
            self._icon_lbl.setPixmap(pixmap)


class _FlowLayout(QLayout):
    """Layout that arranges child widgets horizontally and wraps to subsequent rows when space runs out."""

    def __init__(
        self,
        parent: QWidget | None = None,
        margin: int = 0,
        h_spacing: int = 6,
        v_spacing: int = 6,
    ) -> None:
        super().__init__(parent)
        self._item_list: list = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing
        self.setContentsMargins(margin, margin, margin, margin)

    def addItem(self, item) -> None:
        self._item_list.append(item)

    def horizontalSpacing(self) -> int:
        return self._h_spacing

    def verticalSpacing(self) -> int:
        return self._v_spacing

    def count(self) -> int:
        return len(self._item_list)

    def itemAt(self, index: int):
        if 0 <= index < len(self._item_list):
            return self._item_list[index]
        return None

    def takeAt(self, index: int):
        if 0 <= index < len(self._item_list):
            return self._item_list.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientation:
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect: QRect) -> None:
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self) -> QSize:
        w = self.geometry().width()
        if w > 0:
            return QSize(w, self.heightForWidth(w))
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._item_list:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(+left, +top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._item_list:
            space_x = self.horizontalSpacing()
            space_y = self.verticalSpacing()
            hint = item.sizeHint()
            next_x = x + hint.width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + hint.width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), hint))

            x = next_x
            line_height = max(line_height, hint.height())

        return y + line_height - rect.y() + bottom


class _DayDetailsPanel(_Card):
    """Compact secondary detail section displaying metrics for the selected day."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._date: date = date.today()
        self.setFixedWidth(330)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # 1. Header (Date + Badge)
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        header_col = QVBoxLayout()
        header_col.setSpacing(2)

        self._date_title = QLabel("Wednesday, Oct 14")
        self._date_title.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 15px; font-weight: 700; background: transparent; border: none;"
        )
        header_col.addWidget(self._date_title)

        self._date_subtitle = QLabel("Selected Day")
        self._date_subtitle.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 11px; background: transparent; border: none;"
        )
        header_col.addWidget(self._date_subtitle)
        header_row.addLayout(header_col, 1)

        self._today_badge = QLabel("TODAY")
        self._today_badge.setStyleSheet(
            f"color: #ffffff; background: {_ACCENT}; font-size: 9px; font-weight: 700; "
            f"padding: 3px 7px; border-radius: 4px; border: none;"
        )
        self._today_badge.setVisible(False)
        header_row.addWidget(self._today_badge)

        layout.addLayout(header_row)

        # 2. Metric Cards Container (Clean 2-row layout that NEVER overflows)
        metrics_card = QFrame()
        metrics_card.setStyleSheet(
            f"background: {_CARD_LIGHTER}; border: 1px solid {_CARD_BORDER}; border-radius: 10px;"
        )
        metrics_card_lo = QVBoxLayout(metrics_card)
        metrics_card_lo.setContentsMargins(14, 12, 14, 12)
        metrics_card_lo.setSpacing(10)

        # Row 1: Total Time + Apps Used
        m_row1 = QHBoxLayout()
        m_row1.setSpacing(10)

        # Stat 1: Total Screen Time
        s1_col = QVBoxLayout()
        s1_col.setSpacing(2)
        s1_lbl = QLabel("TOTAL TIME")
        s1_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 700; letter-spacing: 0.08em; border: none;")
        self._stat_time = QLabel("0m")
        self._stat_time.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 15px; font-weight: 700; border: none;")
        s1_col.addWidget(s1_lbl)
        s1_col.addWidget(self._stat_time)
        m_row1.addLayout(s1_col, 1)

        # Divider
        div1 = QFrame()
        div1.setFixedWidth(1)
        div1.setStyleSheet(f"background: {_CARD_BORDER}; border: none;")
        m_row1.addWidget(div1)

        # Stat 2: Apps Count
        s2_col = QVBoxLayout()
        s2_col.setSpacing(2)
        s2_lbl = QLabel("APPS USED")
        s2_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 700; letter-spacing: 0.08em; border: none;")
        self._stat_apps = QLabel("0")
        self._stat_apps.setStyleSheet(f"color: {_TEXT_PRIMARY}; font-size: 15px; font-weight: 700; border: none;")
        s2_col.addWidget(s2_lbl)
        s2_col.addWidget(self._stat_apps)
        m_row1.addLayout(s2_col, 1)

        metrics_card_lo.addLayout(m_row1)

        # Divider line
        h_div = QFrame()
        h_div.setFixedHeight(1)
        h_div.setStyleSheet(f"background: {_CARD_BORDER}; border: none;")
        metrics_card_lo.addWidget(h_div)

        # Row 2: Top Application (Full width, avoids horizontal clipping)
        s3_col = QVBoxLayout()
        s3_col.setSpacing(2)
        s3_lbl = QLabel("TOP APPLICATION")
        s3_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 9px; font-weight: 700; letter-spacing: 0.08em; border: none;")
        self._stat_top_app = QLabel("—")
        self._stat_top_app.setStyleSheet(f"color: {_ACCENT}; font-size: 13px; font-weight: 700; border: none;")
        s3_col.addWidget(s3_lbl)
        s3_col.addWidget(self._stat_top_app)
        metrics_card_lo.addLayout(s3_col)

        layout.addWidget(metrics_card)

        # 3. Category Breakdown (Productivity breakdown)
        self._category_section = QWidget()
        self._category_section.setStyleSheet("background: transparent;")
        cat_lo = QVBoxLayout(self._category_section)
        cat_lo.setContentsMargins(0, 0, 0, 0)
        cat_lo.setSpacing(6)

        cat_header = QLabel("CATEGORIES")
        cat_header.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; letter-spacing: 0.08em; border: none;"
        )
        cat_lo.addWidget(cat_header)

        self._cat_chips_container = QWidget()
        self._cat_chips_container.setStyleSheet("background: transparent;")
        self._cat_flow_layout = _FlowLayout(self._cat_chips_container, margin=0, h_spacing=6, v_spacing=6)
        cat_lo.addWidget(self._cat_chips_container)

        layout.addWidget(self._category_section)

        # 4. Major Application Usage
        app_header_row = QHBoxLayout()
        app_header = QLabel("MAJOR USAGE")
        app_header.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 700; letter-spacing: 0.08em; border: none;"
        )
        app_header_row.addWidget(app_header)
        app_header_row.addStretch(1)

        layout.addLayout(app_header_row)

        self._app_list_layout = QVBoxLayout()
        self._app_list_layout.setSpacing(4)
        layout.addLayout(self._app_list_layout)

        # 5. Empty State Message for Inactive Days
        self._empty_label = QLabel("No activity recorded for this day.")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 12px; font-weight: 500; padding: 28px 0; background: transparent; border: none;"
        )
        self._empty_label.setVisible(False)
        layout.addWidget(self._empty_label)

        layout.addStretch(1)
        self._app_rows: list[_AppUsageRow] = []

    def set_day_data(self, target_date: date, data: ReportsData | None) -> None:
        """Update day details cleanly without flicker."""
        self._date = target_date

        self._date_title.setText(target_date.strftime("%A, %b %d"))
        is_today = (target_date == date.today())
        self._today_badge.setVisible(is_today)
        self._date_subtitle.setText("Today's Activity" if is_today else f"{target_date.strftime('%B %Y')}")

        has_data = data is not None and data.total_screen_time_seconds > 0

        if not has_data:
            self._stat_time.setText("0m")
            self._stat_apps.setText("0")
            self._stat_top_app.setText("—")
            self._category_section.setVisible(False)
            self._clear_category_chips()
            self._empty_label.setVisible(True)
            self._empty_label.setText(
                "No activity recorded for this day."
                if target_date <= date.today()
                else "Future day — no activity yet."
            )
            for r in self._app_rows:
                r.setVisible(False)
        else:
            self._empty_label.setVisible(False)
            self._category_section.setVisible(True)

            self._stat_time.setText(format_duration_compact(data.total_screen_time_seconds))
            self._stat_apps.setText(str(len(data.app_usage)))
            top_app = data.most_used_app_name if data.most_used_app_name != "—" else "None"
            self._stat_top_app.setText(top_app)

            # Category Chips
            self._render_category_chips(data.category_breakdown)

            # App Usage Rows
            top_apps = data.app_usage[:5]
            max_sec = top_apps[0].duration_seconds if top_apps else 1

            self._app_rows = recycle_widgets_in_place(
                layout=self._app_list_layout,
                existing_widgets=self._app_rows,
                new_data=top_apps,
                create_fn=lambda: _AppUsageRow(),
                update_fn=lambda w, item, idx: w.set_app_data(item.app_name, item.duration_seconds, max_sec),
            )

    def _clear_category_chips(self) -> None:
        while self._cat_flow_layout.count():
            item = self._cat_flow_layout.takeAt(0)
            if item:
                wid = item.widget()
                if wid:
                    wid.deleteLater()

    def _render_category_chips(self, categories: list[tuple[str, int, int]]) -> None:
        self._clear_category_chips()
        active_cats = [c for c in categories if c[1] > 0][:4]
        if not active_cats:
            self._category_section.setVisible(False)
            return

        self._category_section.setVisible(True)
        for cat_name, dur, pct in active_cats:
            chip = QFrame()
            chip.setStyleSheet(
                f"background: {_CARD_LIGHTER}; border: 1px solid {_CARD_BORDER}; border-radius: 6px;"
            )
            chip_lo = QHBoxLayout(chip)
            chip_lo.setContentsMargins(7, 4, 9, 4)
            chip_lo.setSpacing(5)

            icon_lbl = QLabel()
            icon_lbl.setFixedSize(14, 14)
            icon_lbl.setPixmap(_get_category_pixmap(cat_name, 14, _ACCENT))
            chip_lo.addWidget(icon_lbl)

            lbl = QLabel(f"{cat_name} {pct}%")
            lbl.setStyleSheet(f"color: {_TEXT_SECONDARY}; font-size: 10px; font-weight: 600; border: none;")
            chip_lo.addWidget(lbl)

            self._cat_flow_layout.addWidget(chip)

        self._cat_chips_container.updateGeometry()

