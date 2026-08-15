"""Timeline page — chronological session history for today.

Premium scrollable feed grouped by hour, matching the Trackora dashboard
design language: dark cards, blue glow accents, smooth hover effects.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from PySide6.QtCore import Qt, QRectF, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import (
    QBrush, QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ...models.dashboard import TimelineSession
from ...utils.grouping import merge_consecutive_sessions

from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from ...database.dashboard import DashboardRepository

__all__ = ["TimelinePage"]

# ─── Color tokens (identical to dashboard) ──────────────────────────────────
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

from trackora.gui.utils import get_app_icon as _get_app_icon

def _get_cached_app_icon(app_name: str, on_loaded=None) -> QPixmap | None:
    return _get_app_icon(app_name, 28, on_loaded=on_loaded)


def _add_shadow(widget: QWidget, blur: int = 20, opacity: int = 35, dy: int = 3):
    pass


def _format_duration_smart(seconds: int) -> str:
    """Duration label that gracefully handles short sessions: 8s, 42s, 3m, 18m, 1h 24m."""
    seconds = max(int(seconds), 0)
    if seconds < 60:
        return f"{seconds}s"
    hours, remainder = divmod(seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _format_time_12h(dt: datetime) -> str:
    """Format datetime to 12-hour time like '3:42 PM'."""
    local = dt.astimezone()
    return local.strftime("%I:%M %p").lstrip("0")


def _hour_label(hour_24: int) -> str:
    """Convert 24h hour to display label like '6 PM', '12 AM'."""
    if hour_24 == 0:
        return "12 AM"
    if hour_24 == 12:
        return "12 PM"
    if hour_24 < 12:
        return f"{hour_24} AM"
    return f"{hour_24 - 12} PM"


from trackora.gui.ui_common import AnimatedToggleSwitch


class _ToggleSwitch(AnimatedToggleSwitch):
    """Custom premium animated toggle switch widget."""

    def __init__(self, callback, parent=None):
        super().__init__(checked=False, on_toggled=callback, parent=parent)


# ─── Summary stat chip ──────────────────────────────────────────────────────

class _SummaryChip(QFrame):
    """Compact summary metric card for the top row."""

    def __init__(self, icon_char: str, caption: str, parent=None):
        super().__init__(parent)
        self.setObjectName("summaryChip")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(
            f"QFrame#summaryChip {{ background: {_CARD}; "
            f"border: 1px solid {_CARD_BORDER}; border-radius: 12px; }}"
        )
        _add_shadow(self, blur=14, opacity=25, dy=2)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        icon = QLabel(icon_char)
        icon.setStyleSheet(
            f"color: {_ACCENT}; font-size: 14px; background: transparent; border: none;"
        )
        top_row.addWidget(icon)

        cap = QLabel(caption)
        cap.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; font-weight: 600; "
            f"letter-spacing: 0.06em; background: transparent; border: none;"
        )
        top_row.addWidget(cap)
        top_row.addStretch(1)
        layout.addLayout(top_row)

        self._value = QLabel("—")
        self._value.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 18px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(self._value)

    def set_value(self, text: str):
        self._value.setText(text)


# ─── Single timeline entry card ─────────────────────────────────────────────

class _TimelineEntryCard(QFrame):
    """Compact card for one session in the timeline feed."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tlCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._hovered = False
        self.setStyleSheet(self._css(_CARD))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 18, 12)
        layout.setSpacing(14)

        # App icon
        self._icon_label = QLabel()
        self._icon_label.setFixedSize(32, 32)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self._icon_label)

        # Name + window title column
        info_col = QVBoxLayout()
        info_col.setContentsMargins(0, 0, 0, 0)
        info_col.setSpacing(2)

        self._name = QLabel("")
        self._name.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 13px; font-weight: 600; "
            f"background: transparent; border: none;"
        )
        info_col.addWidget(self._name)

        self._subtitle = QLabel("")
        self._subtitle.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 11px; "
            f"background: transparent; border: none;"
        )
        self._subtitle.setWordWrap(True)
        info_col.addWidget(self._subtitle)
        layout.addLayout(info_col, 1)

        # Right side: duration + time range
        right_col = QVBoxLayout()
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(2)

        self._duration = QLabel("")
        self._duration.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._duration.setStyleSheet(
            f"color: {_ACCENT}; font-size: 13px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        right_col.addWidget(self._duration)

        self._time_range = QLabel("")
        self._time_range.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._time_range.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; "
            f"background: transparent; border: none;"
        )
        right_col.addWidget(self._time_range)
        layout.addLayout(right_col)

    def _css(self, bg: str) -> str:
        return (
            f"QFrame#tlCard {{ background: {bg}; "
            f"border: 1px solid {_CARD_BORDER}; border-radius: 10px; }}"
        )

    def set_data(self, session: TimelineSession):
        self._name.setText(session.app_name)
        self._duration.setText(_format_duration_smart(session.duration_seconds))

        start_str = _format_time_12h(session.start_time)
        end_str = _format_time_12h(session.end_time)
        self._time_range.setText(f"{start_str} → {end_str}")

        # Window title subtitle (truncated)
        title = session.window_title or ""
        if len(title) > 60:
            title = title[:57] + "…"
        self._subtitle.setText(title)
        self._subtitle.setVisible(bool(title))

        # Icon (cached lookup)
        self._current_app_name = session.app_name
        def _on_icon_ready(pm: QPixmap | None) -> None:
            if pm and not pm.isNull() and getattr(self, "_current_app_name", "") == session.app_name:
                self._icon_label.setPixmap(pm)
                self._icon_label.setStyleSheet("background: transparent; border: none;")

        pixmap = _get_cached_app_icon(session.app_name, on_loaded=_on_icon_ready)
        if pixmap:
            self._icon_label.setPixmap(pixmap)
            self._icon_label.setStyleSheet("background: transparent; border: none;")
        else:
            self._icon_label.setText("●")
            self._icon_label.setStyleSheet(
                f"color: {_ACCENT}; font-size: 16px; "
                f"background: {_CARD_BORDER}; border-radius: 8px; border: none;"
            )

    def update_session_time(self, duration_seconds: int, start_time: datetime, end_time: datetime):
        self._duration.setText(_format_duration_smart(duration_seconds))
        start_str = _format_time_12h(start_time)
        end_str = _format_time_12h(end_time)
        self._time_range.setText(f"{start_str} → {end_str}")

    def enterEvent(self, event):
        self._hovered = True
        self.setStyleSheet(self._css(_CARD_LIGHTER))

    def leaveEvent(self, event):
        self._hovered = False
        self.setStyleSheet(self._css(_CARD))


# ─── Hour section header ────────────────────────────────────────────────────

class _HourHeader(QWidget):
    """Compact hour divider label with decorative line."""

    def __init__(self, hour_text: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)

        label = QLabel(hour_text)
        label.setStyleSheet(
            f"color: {_ACCENT}; font-size: 11px; font-weight: 700; "
            f"letter-spacing: 0.06em; background: transparent; border: none;"
        )
        label.setFixedWidth(60)
        layout.addWidget(label)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Plain)
        line.setFixedHeight(1)
        line.setStyleSheet(f"background-color: {_CARD_BORDER}; border: none;")
        layout.addWidget(line, 1)


# ─── Vertical timeline connector ────────────────────────────────────────────

class _TimelineConnector(QWidget):
    """A subtle vertical line segment between timeline cards."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(2)
        self.setFixedWidth(1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Soft blue vertical dot
        painter.setPen(Qt.PenStyle.NoPen)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor(59, 130, 246, 40))
        grad.setColorAt(0.5, QColor(59, 130, 246, 70))
        grad.setColorAt(1, QColor(59, 130, 246, 40))
        painter.setBrush(QBrush(grad))
        x = self.width() // 2
        painter.drawRect(QRectF(x, 0, 1, self.height()))
        painter.end()


# ─── Entry row with timeline connector ───────────────────────────────────────

class _TimelineEntryRow(QWidget):
    """Wraps a timeline card with a left-side vertical connector dot/line."""

    def __init__(self, session: TimelineSession, is_last: bool = False, parent=None):
        super().__init__(parent)
        self._is_last = is_last

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Left connector column — dot + line
        self._connector = QWidget()
        self._connector.setFixedWidth(16)
        layout.addWidget(self._connector)

        # Card
        self._card = _TimelineEntryCard()
        self._card.set_data(session)
        layout.addWidget(self._card, 1)

    def update_session_time(self, duration_seconds: int, start_time: datetime, end_time: datetime):
        self._card.update_session_time(duration_seconds, start_time, end_time)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = 8  # center of connector column
        h = self.height()
        mid_y = h // 2

        # Vertical line above dot
        if True:
            painter.setPen(QPen(QColor(59, 130, 246, 45), 1.5))
            painter.drawLine(cx, 0, cx, mid_y - 6)

        # Vertical line below dot (except last entry)
        if not self._is_last:
            painter.setPen(QPen(QColor(59, 130, 246, 45), 1.5))
            painter.drawLine(cx, mid_y + 6, cx, h)

        # Glowing dot
        painter.setPen(Qt.PenStyle.NoPen)
        # Outer glow
        glow = QRadialGradient(cx, mid_y, 8)
        glow.setColorAt(0, QColor(59, 130, 246, 50))
        glow.setColorAt(1, QColor(59, 130, 246, 0))
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(QRectF(cx - 8, mid_y - 8, 16, 16))
        # Core dot
        painter.setBrush(QBrush(QColor(59, 130, 246, 200)))
        painter.drawEllipse(QRectF(cx - 3, mid_y - 3, 6, 6))

        painter.end()


# ═══════════════════════════════════════════════════════════════════════════
#  TIMELINE PAGE
# ═══════════════════════════════════════════════════════════════════════════

class TimelinePage(QWidget):
    """Shows a chronological view of all app sessions during the day."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._repository: DashboardRepository | None = None
        self._entry_widgets: list[QWidget] = []
        self._render_queue: list[tuple[str, Any, Any]] = []
        self._rendered_count = 0
        self._last_sessions_sig: tuple | None = None

        # Scroll area
        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background: {_BG}; border: none; }}"
            f"QScrollBar:vertical {{ background: {_BG}; width: 5px; margin: 0; }}"
            f"QScrollBar::handle:vertical {{ background: {_CARD_BORDER}; border-radius: 2px; min-height: 30px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}"
        )
        self._scroll.verticalScrollBar().valueChanged.connect(self._on_scroll)

        self._container = QWidget()
        self._container.setStyleSheet(f"background: {_BG};")
        self._scroll.setWidget(self._container)

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(self._scroll)

        # Floating Back to Top button
        self._back_to_top_btn = QPushButton("▲ TOP", self)
        self._back_to_top_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_to_top_btn.setStyleSheet(
            f"QPushButton {{ background: {_CARD_LIGHTER}; border: 1px solid {_ACCENT}; "
            f"color: {_TEXT_PRIMARY}; font-size: 11px; font-weight: 700; border-radius: 16px; "
            f"padding: 6px 12px; letter-spacing: 0.05em; }}"
            f"QPushButton:hover {{ background: {_ACCENT}; color: #ffffff; }}"
        )
        _add_shadow(self._back_to_top_btn, blur=14, opacity=40, dy=2)
        self._back_to_top_btn.clicked.connect(self._scroll_to_top)
        self._back_to_top_btn.hide()

        main = QVBoxLayout(self._container)
        main.setContentsMargins(32, 20, 32, 32)
        main.setSpacing(18)

        # ── Header ──────────────────────────────────────────────────────
        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(0)

        header_left = QVBoxLayout()
        header_left.setSpacing(4)

        title = QLabel("Timeline")
        title.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 22px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        header_left.addWidget(title)

        subtitle = QLabel("Today's activity feed")
        subtitle.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 13px; "
            f"background: transparent; border: none;"
        )
        header_left.addWidget(subtitle)
        header_row.addLayout(header_left, 1)

        # Toggle Switch on the right side
        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(8)
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        toggle_label = QLabel("Detailed Sessions")
        toggle_label.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 12px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        toggle_layout.addWidget(toggle_label)

        self._detailed_toggle = _ToggleSwitch(self._on_toggle_detailed)
        toggle_layout.addWidget(self._detailed_toggle)

        header_row.addLayout(toggle_layout)
        main.addLayout(header_row)

        # ── Summary row ─────────────────────────────────────────────────
        summary_row = QHBoxLayout()
        summary_row.setSpacing(12)

        self._chip_sessions = _SummaryChip("⊞", "SESSIONS TODAY")
        self._chip_longest = _SummaryChip("◷", "LONGEST SESSION")
        self._chip_most_used = _SummaryChip("◎", "MOST USED APP")

        summary_row.addWidget(self._chip_sessions, 1)
        summary_row.addWidget(self._chip_longest, 1)
        summary_row.addWidget(self._chip_most_used, 1)
        main.addLayout(summary_row)

        # ── Feed container ──────────────────────────────────────────────
        self._feed_layout = QVBoxLayout()
        self._feed_layout.setSpacing(0)
        main.addLayout(self._feed_layout)

        # ── Empty state (shown when no sessions) ────────────────────────
        self._empty_state = QWidget()
        empty_layout = QVBoxLayout(self._empty_state)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(10)
        empty_layout.setContentsMargins(0, 60, 0, 60)

        empty_icon = QLabel("◔")
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_icon.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 36px; background: transparent; border: none;"
        )
        empty_layout.addWidget(empty_icon)

        empty_title = QLabel("No activity recorded yet")
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_title.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 15px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        empty_layout.addWidget(empty_title)

        empty_sub = QLabel("Start using apps and your timeline will appear here")
        empty_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_sub.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 12px; background: transparent; border: none;"
        )
        empty_layout.addWidget(empty_sub)

        self._empty_state.setVisible(False)
        main.addWidget(self._empty_state)

        # Show More Button Container (Compact 130px centered button)
        self._show_more_container = QWidget()
        sm_layout = QHBoxLayout(self._show_more_container)
        sm_layout.setContentsMargins(0, 12, 0, 12)
        sm_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._show_more_btn = QPushButton("Show More")
        self._show_more_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._show_more_btn.setFixedSize(130, 34)
        self._show_more_btn.setStyleSheet(
            f"QPushButton {{ background: {_CARD}; border: 1px solid {_CARD_BORDER}; "
            f"color: {_ACCENT}; font-size: 12px; font-weight: 600; border-radius: 6px; }}"
            f"QPushButton:hover {{ background: {_CARD_LIGHTER}; border-color: {_ACCENT}; color: #ffffff; }}"
        )
        self._show_more_btn.clicked.connect(self._on_show_more_clicked)
        sm_layout.addWidget(self._show_more_btn)
        self._show_more_container.hide()
        main.addWidget(self._show_more_container)

        main.addStretch(1)
        self._main_layout = main
        self._limit = 50

    def set_repository(self, repo: DashboardRepository):
        """Called by MainWindow to inject the shared repository."""
        self._repository = repo

    def reset_pagination(self):
        """Reset pagination to default 50 sessions when navigating pages."""
        if self._limit != 50:
            self._limit = 50
            self._last_structure_sig = None

    def refresh_data(self, force: bool = False):
        """Reload timeline sessions from the database."""
        if self._repository is None:
            return

        sessions = self._repository.load_timeline_sessions()

        if not self._detailed_toggle.is_checked():
            sessions = merge_consecutive_sessions(sessions, descending=True)

        total_sessions = len(sessions)
        displayed_sessions = sessions[:self._limit]

        # Structural signature: app_name, window_title, start_time, and limit
        structure_sig = tuple(
            (s.app_name, s.window_title, s.start_time)
            for s in displayed_sessions
        ) + (self._limit,)

        # If structure is unchanged during polling tick, update active top session in-place with zero lag!
        if not force and getattr(self, "_last_structure_sig", None) == structure_sig:
            self._update_summary(sessions)
            if displayed_sessions and getattr(self, "_first_session_row", None):
                active_s = displayed_sessions[0]
                self._first_session_row.update_session_time(
                    active_s.duration_seconds,
                    active_s.start_time,
                    active_s.end_time
                )
            return

        self._last_structure_sig = structure_sig

        scrollbar = self._scroll.verticalScrollBar()
        saved_scroll = scrollbar.value()

        self.setUpdatesEnabled(False)
        self._clear_feed()
        self._first_session_row = None

        if not sessions:
            self._update_summary([])
            self._empty_state.setVisible(True)
            self._show_more_container.hide()
            self.setUpdatesEnabled(True)
            return

        self._empty_state.setVisible(False)
        self._update_summary(sessions)

        # Group displayed sessions by hour (local time), sorted newest hour first
        hour_groups: dict[int, list[TimelineSession]] = defaultdict(list)
        for session in displayed_sessions:
            local_start = session.start_time.astimezone()
            hour_groups[local_start.hour].append(session)

        sorted_hours = sorted(hour_groups.keys(), reverse=True)

        for hour in sorted_hours:
            header = _HourHeader(_hour_label(hour))
            self._feed_layout.addWidget(header)
            self._entry_widgets.append(header)

            group = hour_groups[hour]
            group.sort(key=lambda s: s.start_time, reverse=True)

            for i, session in enumerate(group):
                is_last_in_group = (i == len(group) - 1) and (hour == sorted_hours[-1])
                row = _TimelineEntryRow(session, is_last=is_last_in_group)
                if self._first_session_row is None:
                    self._first_session_row = row
                self._feed_layout.addWidget(row)
                self._entry_widgets.append(row)

        if total_sessions > self._limit:
            self._show_more_container.show()
        else:
            self._show_more_container.hide()

        self.setUpdatesEnabled(True)

        if saved_scroll > 0:
            scrollbar.setValue(min(saved_scroll, scrollbar.maximum()))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "_back_to_top_btn"):
            btn_w, btn_h = 76, 32
            self._back_to_top_btn.setGeometry(
                self.width() - btn_w - 24,
                self.height() - btn_h - 24,
                btn_w,
                btn_h
            )
            self._back_to_top_btn.raise_()

    def _scroll_to_top(self):
        """Smoothly scroll to top using QPropertyAnimation."""
        scrollbar = self._scroll.verticalScrollBar()
        if scrollbar.value() == 0:
            return
        if not hasattr(self, "_scroll_anim"):
            self._scroll_anim = QPropertyAnimation(scrollbar, b"value", self)
            self._scroll_anim.setDuration(250)
            self._scroll_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._scroll_anim.stop()
        self._scroll_anim.setStartValue(scrollbar.value())
        self._scroll_anim.setEndValue(0)
        self._scroll_anim.start()

    def _on_scroll(self, value):
        """Toggle Back to Top button based on scroll position."""
        if hasattr(self, "_back_to_top_btn"):
            if value > 250:
                self._back_to_top_btn.show()
                self._back_to_top_btn.raise_()
            else:
                self._back_to_top_btn.hide()

    def _on_show_more_clicked(self):
        self._limit += 50
        self.refresh_data(force=True)

    def _clear_feed(self):
        """Remove all dynamically created timeline entries."""
        self.setUpdatesEnabled(False)
        for widget in self._entry_widgets:
            self._feed_layout.removeWidget(widget)
            widget.deleteLater()
        self._entry_widgets.clear()
        self.setUpdatesEnabled(True)

    def _update_summary(self, sessions: list[TimelineSession]):
        """Update the summary chips with today's stats."""
        count = len(sessions)
        self._chip_sessions.set_value(str(count))

        if sessions:
            longest = max(sessions, key=lambda s: s.duration_seconds)
            self._chip_longest.set_value(_format_duration_smart(longest.duration_seconds))

            # Most used app by total duration
            app_totals: dict[str, int] = defaultdict(int)
            for s in sessions:
                app_totals[s.app_name] += s.duration_seconds
            most_used = max(app_totals, key=lambda k: app_totals[k])
            self._chip_most_used.set_value(most_used)
        else:
            self._chip_longest.set_value("—")
            self._chip_most_used.set_value("—")

    def _on_toggle_detailed(self, checked: bool):
        self._last_sessions_sig = None
        self.refresh_data()


