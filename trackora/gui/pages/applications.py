"""Applications page — beautiful app usage explorer.

Matches the dashboard's visual language: same color tokens, card depth,
typography hierarchy, icon system, and hover interactions.
"""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import (
    QBrush, QColor, QIcon, QLinearGradient, QPainter, QPen, QPixmap,
)
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from ...database.dashboard import DashboardRepository
from ...models.dashboard import AppDetailedStats
from ...utils.formatting import format_duration_compact

# ─── Shared color tokens (identical to dashboard.py) ────────────────────────
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

# ─── Icon theme lookup (shared with dashboard) ─────────────────────────────
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


def _add_shadow(widget: QWidget, blur: int = 20, opacity: int = 35, dy: int = 3):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, opacity))
    shadow.setOffset(0, dy)
    widget.setGraphicsEffect(shadow)


def _format_last_active(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    local = dt.astimezone()
    return local.strftime("%I:%M %p").lstrip("0").lower()


# ─── Range pill button ──────────────────────────────────────────────────────

class _RangePill(QWidget):
    """Rounded pill button for range selection (Today / 7 Days / 30 Days)."""

    def __init__(self, label: str, days: int, callback, parent=None):
        super().__init__(parent)
        self._days = days
        self._callback = callback
        self._active = False
        self._hovered = False
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        self._label = QLabel(label)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._label)
        self._apply_style()

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def _apply_style(self):
        if self._active:
            bg, text_c = _ACCENT_SOFT, _TEXT_PRIMARY
        elif self._hovered:
            bg, text_c = _CARD_LIGHTER, _TEXT_PRIMARY
        else:
            bg, text_c = _CARD, _TEXT_SECONDARY
        self.setStyleSheet(
            f"background: {bg}; border-radius: 8px; border: 1px solid {_CARD_BORDER};"
        )
        self._label.setStyleSheet(
            f"color: {text_c}; font-size: 12px; font-weight: 500; "
            f"background: transparent; border: none;"
        )

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style()

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style()

    def mousePressEvent(self, event):
        self._callback(self._days)


# ─── Application card ──────────────────────────────────────────────────────

class _AppCard(QFrame):
    """Expandable application usage card with icon, stats, and progress bar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("appCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self._hovered = False
        self._expanded = False
        self._bar_ratio = 0.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(self._card_css(_CARD))
        _add_shadow(self, blur=16, opacity=30, dy=2)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(0)

        # ── Main row ────────────────────────────────────────────────────
        self._main_row = QWidget()
        row_layout = QHBoxLayout(self._main_row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(14)

        # Icon
        self._icon_label = QLabel()
        self._icon_label.setFixedSize(36, 36)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("background: transparent; border: none;")
        row_layout.addWidget(self._icon_label)

        # Name + meta column
        name_col = QVBoxLayout()
        name_col.setContentsMargins(0, 0, 0, 0)
        name_col.setSpacing(3)

        self._name = QLabel("")
        self._name.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 14px; font-weight: 600; "
            f"background: transparent; border: none;"
        )
        name_col.addWidget(self._name)

        self._meta = QLabel("")
        self._meta.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 11px; "
            f"background: transparent; border: none;"
        )
        name_col.addWidget(self._meta)
        row_layout.addLayout(name_col, 1)

        # Duration (right side)
        self._duration = QLabel("")
        self._duration.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._duration.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 15px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        row_layout.addWidget(self._duration)

        main_layout.addWidget(self._main_row)

        # ── Progress bar ────────────────────────────────────────────────
        self._bar_widget = QWidget()
        self._bar_widget.setFixedHeight(3)
        main_layout.addSpacing(10)
        main_layout.addWidget(self._bar_widget)

        # ── Expandable detail area ──────────────────────────────────────
        self._detail_widget = QWidget()
        self._detail_widget.setVisible(False)
        detail_layout = QHBoxLayout(self._detail_widget)
        detail_layout.setContentsMargins(50, 12, 0, 4)
        detail_layout.setSpacing(32)

        self._stat_sessions = self._make_stat("Sessions")
        self._stat_avg = self._make_stat("Avg Session")
        self._stat_last = self._make_stat("Last Active")

        detail_layout.addLayout(self._stat_sessions[0])
        detail_layout.addLayout(self._stat_avg[0])
        detail_layout.addLayout(self._stat_last[0])
        detail_layout.addStretch(1)

        main_layout.addWidget(self._detail_widget)

    def _make_stat(self, caption: str) -> tuple:
        """Create a stat column: returns (layout, value_label)."""
        col = QVBoxLayout()
        col.setSpacing(2)
        val = QLabel("—")
        val.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 13px; font-weight: 600; "
            f"background: transparent; border: none;"
        )
        col.addWidget(val)
        cap = QLabel(caption)
        cap.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; "
            f"background: transparent; border: none;"
        )
        col.addWidget(cap)
        return (col, val)

    def _card_css(self, bg: str) -> str:
        return (
            f"QFrame#appCard {{ background: {bg}; "
            f"border: 1px solid {_CARD_BORDER}; border-radius: 12px; }}"
        )

    def set_data(self, stat: AppDetailedStats, ratio: float):
        self._bar_ratio = max(0.0, min(ratio, 1.0))
        self._name.setText(stat.app_name)
        self._duration.setText(format_duration_compact(stat.duration_seconds))
        self._meta.setText(
            f"{stat.session_count} session{'s' if stat.session_count != 1 else ''}  ·  "
            f"Last active {_format_last_active(stat.last_active)}"
        )
        # Stats
        self._stat_sessions[1].setText(str(stat.session_count))
        self._stat_avg[1].setText(format_duration_compact(stat.avg_session_seconds))
        self._stat_last[1].setText(_format_last_active(stat.last_active))
        # Icon
        pixmap = _get_app_icon(stat.app_name, 32)
        if pixmap:
            self._icon_label.setPixmap(pixmap)
        else:
            self._icon_label.setText("●")
            self._icon_label.setStyleSheet(
                f"color: {_ACCENT}; font-size: 18px; "
                f"background: {_CARD_BORDER}; border-radius: 8px; border: none;"
            )
        self.update()

    def enterEvent(self, event):
        self._hovered = True
        self.setStyleSheet(self._card_css(_CARD_LIGHTER))

    def leaveEvent(self, event):
        self._hovered = False
        self.setStyleSheet(self._card_css(_CARD))

    def mousePressEvent(self, event):
        self._expanded = not self._expanded
        self._detail_widget.setVisible(self._expanded)

    def paintEvent(self, event):
        super().paintEvent(event)
        bw = self._bar_widget
        if bw.width() < 2:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pos = bw.mapTo(self, bw.rect().topLeft())
        x, y, w, h = pos.x(), pos.y(), bw.width(), bw.height()
        # Track
        painter.setBrush(QBrush(QColor(_CARD_BORDER)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(x, y, w, h), 1.5, 1.5)
        # Fill
        fill_w = w * self._bar_ratio
        if fill_w > 0:
            grad = QLinearGradient(x, y, x + fill_w, y)
            grad.setColorAt(0, QColor("#2563eb"))
            grad.setColorAt(1, QColor("#60a5fa"))
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(QRectF(x, y, fill_w, h), 1.5, 1.5)
        painter.end()


# ─── Empty state ────────────────────────────────────────────────────────────

class _EmptyState(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        icon = QLabel("⊞")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 32px; background: transparent; border: none;"
        )
        layout.addWidget(icon)

        title = QLabel("No application usage tracked yet")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 14px; font-weight: 500; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(title)

        sub = QLabel("Start using apps and Trackora will show your usage here")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 12px; background: transparent; border: none;"
        )
        layout.addWidget(sub)


# ═══════════════════════════════════════════════════════════════════════════
#  APPLICATIONS PAGE
# ═══════════════════════════════════════════════════════════════════════════

class ApplicationsPage(QWidget):
    """Per-application usage explorer — premium polished design."""

    _RANGE_OPTIONS = [
        ("Today", 1),
        ("Last 7 Days", 7),
        ("Last 30 Days", 30),
    ]

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._repository: DashboardRepository | None = None
        self._current_days = 1
        self._app_cards: list[_AppCard] = []

        # Scroll area
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

        self._container = QWidget()
        self._container.setStyleSheet(f"background: {_BG};")
        scroll.setWidget(self._container)

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        main = QVBoxLayout(self._container)
        main.setContentsMargins(32, 20, 32, 32)
        main.setSpacing(20)

        # ── Header ──────────────────────────────────────────────────────
        header = QVBoxLayout()
        header.setSpacing(4)

        title = QLabel("Applications")
        title.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 22px; font-weight: 700; "
            f"background: transparent; border: none;"
        )
        header.addWidget(title)

        subtitle = QLabel("See where your time goes")
        subtitle.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 13px; "
            f"background: transparent; border: none;"
        )
        header.addWidget(subtitle)
        main.addLayout(header)

        # ── Range pills + count ─────────────────────────────────────────
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self._pills: list[_RangePill] = []
        for label, days in self._RANGE_OPTIONS:
            pill = _RangePill(label, days, self._on_range_change)
            self._pills.append(pill)
            filter_row.addWidget(pill)

        filter_row.addStretch(1)

        self._count_label = QLabel("")
        self._count_label.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 12px; "
            f"background: transparent; border: none;"
        )
        filter_row.addWidget(self._count_label)

        main.addLayout(filter_row)

        # ── App cards container ─────────────────────────────────────────
        self._cards_layout = QVBoxLayout()
        self._cards_layout.setSpacing(10)
        main.addLayout(self._cards_layout)

        # ── Empty state (hidden by default) ─────────────────────────────
        self._empty_state = _EmptyState()
        self._empty_state.setVisible(False)
        main.addWidget(self._empty_state)

        main.addStretch(1)

        # Set default active pill
        self._pills[0].set_active(True)

    def set_repository(self, repo: DashboardRepository):
        """Called by MainWindow to inject the shared repository."""
        self._repository = repo

    def refresh_data(self):
        """Reload app data for the current range."""
        if self._repository is None:
            return

        stats = self._repository.load_app_details(days=self._current_days)

        # Clear existing cards
        for card in self._app_cards:
            self._cards_layout.removeWidget(card)
            card.deleteLater()
        self._app_cards.clear()

        if not stats:
            self._empty_state.setVisible(True)
            self._count_label.setText("")
            return

        self._empty_state.setVisible(False)
        self._count_label.setText(f"{len(stats)} applications")

        max_secs = stats[0].duration_seconds if stats else 1
        for stat in stats:
            card = _AppCard()
            ratio = stat.duration_seconds / max(max_secs, 1)
            card.set_data(stat, ratio)
            self._cards_layout.addWidget(card)
            self._app_cards.append(card)

    def _on_range_change(self, days: int):
        self._current_days = days
        for pill in self._pills:
            pill.set_active(pill._days == days)
        self.refresh_data()
