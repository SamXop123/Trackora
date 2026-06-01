"""Timeline page — chronological session history for today.

Premium scrollable feed grouped by hour, matching the Trackora dashboard
design language: dark cards, blue glow accents, smooth hover effects.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import (
    QBrush, QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ...models.dashboard import TimelineSession
from ...utils.grouping import merge_consecutive_sessions

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ...database.dashboard import DashboardRepository

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

# ─── Icon theme lookup (shared) ─────────────────────────────────────────────
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


_ICON_CACHE: dict[tuple[str, int], QPixmap | None] = {}


def _get_app_icon(app_name: str, size: int = 24) -> QPixmap | None:
    cache_key = (app_name, size)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    candidates = _ICON_THEME_MAP.get(app_name, [app_name.lower().replace(" ", "-")])
    if isinstance(candidates, str):
        candidates = [candidates]
    for name in candidates:
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            pm = icon.pixmap(QSize(size, size))
            _ICON_CACHE[cache_key] = pm
            return pm
    fallback = QIcon.fromTheme(_FALLBACK_ICON)
    if not fallback.isNull():
        pm = fallback.pixmap(QSize(size, size))
        _ICON_CACHE[cache_key] = pm
        return pm
    _ICON_CACHE[cache_key] = None
    return None


def _add_shadow(widget: QWidget, blur: int = 20, opacity: int = 35, dy: int = 3):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, opacity))
    shadow.setOffset(0, dy)
    widget.setGraphicsEffect(shadow)


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


class _ToggleSwitch(QWidget):
    """Custom premium toggle switch widget."""

    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.setFixedSize(38, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._checked = False
        self._callback = callback

    def is_checked(self) -> bool:
        return self._checked

    def set_checked(self, checked: bool):
        if self._checked != checked:
            self._checked = checked
            self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self.update()
        self._callback(self._checked)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw background track
        track_color = QColor("#2563eb") if self._checked else QColor("#1c2735")
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)

        # Draw knob
        knob_color = QColor("#e6edf5") if self._checked else QColor("#8b9bb4")
        painter.setBrush(QBrush(knob_color))
        knob_x = self.width() - 17 if self._checked else 3
        painter.drawEllipse(knob_x, 3, 14, 14)
        painter.end()


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
        _add_shadow(self, blur=12, opacity=22, dy=2)

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
        self._duration.setAlignment(Qt.AlignRight)
        self._duration.setStyleSheet(
            f"color: {_ACCENT}; font-size: 13px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        right_col.addWidget(self._duration)

        self._time_range = QLabel("")
        self._time_range.setAlignment(Qt.AlignRight)
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

        # Icon
        pixmap = _get_app_icon(session.app_name, 28)
        if pixmap:
            self._icon_label.setPixmap(pixmap)
        else:
            self._icon_label.setText("●")
            self._icon_label.setStyleSheet(
                f"color: {_ACCENT}; font-size: 16px; "
                f"background: {_CARD_BORDER}; border-radius: 8px; border: none;"
            )

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
        card = _TimelineEntryCard()
        card.set_data(session)
        layout.addWidget(card, 1)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

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
        self._render_queue: list[tuple[str, any, any]] = []
        self._rendered_count = 0

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

        main.addStretch(1)
        self._main_layout = main

    def set_repository(self, repo: DashboardRepository):
        """Called by MainWindow to inject the shared repository."""
        self._repository = repo

    def refresh_data(self):
        """Reload timeline sessions from the database."""
        if self._repository is None:
            return

        sessions = self._repository.load_timeline_sessions()
        self._clear_feed()

        if not sessions:
            self._update_summary([])
            self._empty_state.setVisible(True)
            return

        self._empty_state.setVisible(False)

        if not self._detailed_toggle.is_checked():
            sessions = merge_consecutive_sessions(sessions, descending=True)

        self._update_summary(sessions)

        # Build render queue
        self._render_queue = []
        self._rendered_count = 0

        # Group sessions by hour (local time), sorted newest hour first
        hour_groups: dict[int, list[TimelineSession]] = defaultdict(list)
        for session in sessions:
            local_start = session.start_time.astimezone()
            hour_groups[local_start.hour].append(session)

        sorted_hours = sorted(hour_groups.keys(), reverse=True)

        for hour in sorted_hours:
            self._render_queue.append(('header', _hour_label(hour), None))

            group = hour_groups[hour]
            # Sort sessions within hour: newest first
            group.sort(key=lambda s: s.start_time, reverse=True)

            for i, session in enumerate(group):
                is_last_in_group = (i == len(group) - 1) and (hour == sorted_hours[-1])
                self._render_queue.append(('session', session, is_last_in_group))

        # Scroll to top first to prevent immediate scroll triggers during rendering
        self._scroll.verticalScrollBar().setValue(0)

        # Initial batch loading
        self._load_next_batch(initial=True)

    def _on_scroll(self, value):
        """Trigger loading more items when the user scrolls near the bottom."""
        scrollbar = self._scroll.verticalScrollBar()
        # If we are close to the bottom (less than 150px remaining)
        if value > scrollbar.maximum() - 150:
            self._load_next_batch()

    def _load_next_batch(self, initial=False):
        """Render a small slice of items from the render queue."""
        if not self._render_queue:
            return

        batch_size = 100 if initial else 50
        end_idx = min(self._rendered_count + batch_size, len(self._render_queue))

        if self._rendered_count >= len(self._render_queue):
            return

        # Suspend paint updates during batch layout insertions for maximum performance
        self.setUpdatesEnabled(False)

        for idx in range(self._rendered_count, end_idx):
            item_type, data, extra = self._render_queue[idx]
            if item_type == 'header':
                header = _HourHeader(data)
                self._feed_layout.addWidget(header)
                self._entry_widgets.append(header)
            elif item_type == 'session':
                row = _TimelineEntryRow(data, is_last=extra)
                self._feed_layout.addWidget(row)
                self._entry_widgets.append(row)

        self._rendered_count = end_idx
        self.setUpdatesEnabled(True)

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
        self.refresh_data()


