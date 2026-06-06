"""Main application window for Trackora.

Architecture: MainWindow → _Sidebar + QStackedWidget[pages]
Backend wiring: DashboardRepository → QTimer → DashboardPage.refresh/tick
"""

from __future__ import annotations

from pathlib import Path

from datetime import date, timedelta
from PySide6.QtCore import Qt, QRectF, QTimer, QVariantAnimation
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QIcon, QPixmap, QLinearGradient, QRadialGradient
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel,
    QMainWindow, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget, QPushButton
)

from trackora.database.dashboard import DashboardRepository
from trackora.gui.pages import (
    ApplicationsPage, DashboardPage, GoalsPage,
    InsightsPage, ReportsPage, SettingsPage, TimelinePage,
)

# ── Color tokens ─────────────────────────────────────────────────────────────
_BG = "#0d1117"
_SIDEBAR_BG = "#0f1419"
_SIDEBAR_BORDER = "#1a2332"
_TEXT_PRIMARY = "#e6edf5"
_TEXT_SECONDARY = "#8b9bb4"
_TEXT_MUTED = "#566a82"
_ACCENT = "#3b82f6"
_NAV_ACTIVE_BG = "#152035"
_NAV_HOVER_BG = "#121b28"

# ── Navigation definitions ──────────────────────────────────────────────────
_NAV_ITEMS: list[tuple[str, str]] = [
    ("Dashboard",    "⌂"),
    ("Timeline",     "◔"),
    ("Applications", "⊞"),
    ("Insights",     "◈"),
    ("Goals",        "◎"),
    ("Reports",      "◷"),
]


class _NavButton(QWidget):
    """Sidebar navigation item with icon, label, active indicator, and smooth ambient hover animation."""

    def __init__(self, text: str, icon_char: str, index: int, callback, parent=None):
        super().__init__(parent)
        self._index = index
        self._callback = callback
        self._active = False
        self._hovered = False
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # Ambient hover fade animation
        self._hover_anim = QVariantAnimation(self)
        self._hover_anim.setDuration(180)  # smooth 180ms
        self._hover_anim.setStartValue(0.0)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.valueChanged.connect(self._on_anim_value_changed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(14)

        self._icon = QLabel(icon_char)
        self._icon.setFixedWidth(24)
        self._icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon)

        self._label = QLabel(text)
        layout.addWidget(self._label)
        layout.addStretch(1)
        self._apply_style()

    def set_active(self, active: bool):
        if self._active != active:
            self._active = active
            self._apply_style()
            self.update()

    def _apply_style(self):
        if self._active:
            text_c, icon_c = _TEXT_PRIMARY, _ACCENT
        elif self._hovered:
            text_c, icon_c = _TEXT_PRIMARY, _TEXT_SECONDARY
        else:
            text_c, icon_c = _TEXT_SECONDARY, _TEXT_MUTED

        self._icon.setStyleSheet(
            f"color: {icon_c}; font-size: 20px; background: transparent; border: none;"
        )
        self._label.setStyleSheet(
            f"color: {text_c}; font-size: 12px; font-weight: 500; "
            f"background: transparent; border: none;"
        )

    def _on_anim_value_changed(self, val: float):
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw ambient background & subtle border
        r_val = self._hover_anim.currentValue()
        if self._active:
            bg_color = QColor("#152035")
            border_color = QColor(59, 130, 246, int(255 * 0.15))
        else:
            # Animate from transparent (0 alpha) to hover background color
            bg_color = QColor(18, 27, 40, int(255 * r_val))
            border_color = QColor(139, 155, 180, int(255 * 0.05 * r_val))

        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 1.0))
        
        rect = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        painter.drawRoundedRect(rect, 8.0, 8.0)

        # Draw active indicator line on the left
        if self._active:
            painter.setBrush(QBrush(QColor(_ACCENT)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(QRectF(3, 12, 3, self.height() - 24), 1.5, 1.5)

        painter.end()

    def enterEvent(self, event):
        self._hovered = True
        self._apply_style()
        self._hover_anim.setDirection(QVariantAnimation.Direction.Forward)
        self._hover_anim.start()

    def leaveEvent(self, event):
        self._hovered = False
        self._apply_style()
        self._hover_anim.setDirection(QVariantAnimation.Direction.Backward)
        self._hover_anim.start()

    def mousePressEvent(self, event):
        self._callback(self._index)


class _QuoteCard(QWidget):
    """Custom quote card displaying a motivational message with a premium glowing ray decoration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(120)
        
        ql = QVBoxLayout(self)
        ql.setContentsMargins(16, 14, 16, 25)
        ql.setSpacing(6)

        qm = QLabel("❝")
        qm.setStyleSheet(
            f"color: {_ACCENT}; font-size: 24px; font-weight: bold; background: transparent; border: none;"
        )
        ql.addWidget(qm)

        qt = QLabel("Focus is the\nfoundation of\nmeaningful progress.")
        qt.setWordWrap(True)
        qt.setStyleSheet(
            f"color: {_TEXT_SECONDARY}; font-size: 11px; font-weight: 500; "
            f"background: transparent; border: none; line-height: 1.4;"
        )
        ql.addWidget(qt)
        ql.addStretch(1)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        rect = QRectF(0, 0, self.width(), self.height())
        painter.setBrush(QBrush(QColor(255, 255, 255, 4)))
        painter.setPen(QPen(QColor(255, 255, 255, 8), 1))
        painter.drawRoundedRect(rect.adjusted(0.5, 0.5, -0.5, -0.5), 12, 12)
        
        y = self.height() - 22
        w = self.width()
        
        line_grad = QLinearGradient(0, y, w, y)
        line_grad.setColorAt(0, QColor(59, 130, 246, 0))
        line_grad.setColorAt(0.3, QColor(59, 130, 246, 30))
        line_grad.setColorAt(0.5, QColor(59, 130, 246, 200))
        line_grad.setColorAt(0.7, QColor(59, 130, 246, 30))
        line_grad.setColorAt(1, QColor(59, 130, 246, 0))
        
        painter.setPen(QPen(QBrush(line_grad), 1.5))
        painter.drawLine(15, y, w - 15, y)
        
        cx, cy = w / 2, y
        for radius, alpha in [(12, 20), (7, 60), (3, 180), (1.5, 255)]:
            orb_grad = QRadialGradient(cx, cy, radius)
            orb_grad.setColorAt(0, QColor(59, 130, 246, alpha))
            orb_grad.setColorAt(1, QColor(59, 130, 246, 0))
            painter.setBrush(QBrush(orb_grad))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QRectF(cx - radius, cy - radius, radius * 2, radius * 2))
            
        painter.end()


class _Sidebar(QWidget):
    """Vertical navigation sidebar."""

    def __init__(self, navigate_callback, parent=None):
        super().__init__(parent)
        self.setFixedWidth(185)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"background: {_SIDEBAR_BG}; border-right: 1px solid {_SIDEBAR_BORDER};"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 18, 10, 14)
        layout.setSpacing(3)

        # Branding
        brand_container = QWidget()
        brand_container.setStyleSheet("background: transparent;")
        brand_container_layout = QVBoxLayout(brand_container)
        brand_container_layout.setContentsMargins(8, 0, 8, 12)
        brand_container_layout.setSpacing(0)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        brand_row.setContentsMargins(0, 0, 0, 0)

        brand_icon = QLabel()
        logo_path = Path(__file__).resolve().parents[2] / "assets" / "trackora_logo.png"
        if logo_path.exists():
            px = QPixmap(str(logo_path))
            brand_icon.setPixmap(px.scaled(26, 26, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            brand_icon.setText("◉")
            brand_icon.setStyleSheet(
                f"color: {_ACCENT}; font-size: 18px; background: transparent; border: none;"
            )
        brand_row.addWidget(brand_icon)

        brand_text = QLabel("Trackora")
        brand_text.setStyleSheet(
            f"color: {_TEXT_PRIMARY}; font-size: 16px; font-weight: 800; "
            f"letter-spacing: 0.05em; background: transparent; border: none;"
        )
        brand_row.addWidget(brand_text)
        brand_row.addStretch(1)
        brand_container_layout.addLayout(brand_row)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFrameShadow(QFrame.Shadow.Plain)
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background-color: {_SIDEBAR_BORDER}; border: none; margin-top: 12px;")
        brand_container_layout.addWidget(divider)

        layout.addWidget(brand_container)
        layout.addSpacing(12)

        # Nav items
        self._buttons: list[_NavButton] = []
        for i, (label, icon) in enumerate(_NAV_ITEMS):
            btn = _NavButton(label, icon, i, navigate_callback)
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch(1)

        # Quote
        quote_card = _QuoteCard()
        layout.addWidget(quote_card)
        layout.addSpacing(12)

        # Settings
        settings_btn = _NavButton("Settings", "⚙", len(_NAV_ITEMS), navigate_callback)
        self._buttons.append(settings_btn)
        layout.addWidget(settings_btn)
        self.set_active(0)

    def set_active(self, index: int):
        for btn in self._buttons:
            btn.set_active(btn._index == index)


class MainWindow(QMainWindow):
    """Top-level Trackora application window."""

    def __init__(self, *, database_path: Path, refresh_seconds: int):
        super().__init__()
        self._repository = DashboardRepository(database_path)
        self._refresh_seconds = refresh_seconds
        self._selected_date = date.today()
        self._tracking_paused = False

        self.setWindowTitle("Trackora")
        logo_path = Path(__file__).resolve().parents[2] / "assets" / "trackora_logo.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))
        self.resize(1280, 820)
        self.setMinimumSize(1024, 680)

        self._build_layout()
        self._apply_base_style()
        self._start_timers()
        self._refresh_dashboard()

    def _build_layout(self):
        root = QWidget(self)
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._sidebar = _Sidebar(self._on_nav_click)
        root_layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        root_layout.addWidget(self._stack, 1)

        self._dashboard_page = DashboardPage()
        self._dashboard_page.set_repository(self._repository)
        self._dashboard_page.date_changed.connect(self._on_dashboard_date_changed)
        self._dashboard_page.reset_date_requested.connect(self._on_dashboard_reset_date)
        self._dashboard_page.view_all_requested.connect(lambda: self._on_nav_click(2))
        self._dashboard_page.stop_clicked.connect(self._on_dashboard_stop_clicked)
        self._stack.addWidget(self._dashboard_page)      # 0
        self._timeline_page = TimelinePage()
        self._timeline_page.set_repository(self._repository)
        self._stack.addWidget(self._timeline_page)            # 1
        self._apps_page = ApplicationsPage()
        self._apps_page.set_repository(self._repository)
        self._stack.addWidget(self._apps_page)            # 2
        self._insights_page = InsightsPage()
        self._insights_page.set_repository(self._repository)
        self._stack.addWidget(self._insights_page)        # 3
        self._stack.addWidget(GoalsPage())                # 4
        self._reports_page = ReportsPage()
        self._reports_page.set_repository(self._repository)
        self._stack.addWidget(self._reports_page)          # 5
        
        self._settings_page = SettingsPage()
        self._settings_page.set_repository(self._repository)
        self._stack.addWidget(self._settings_page)         # 6

        self._stack.setCurrentIndex(0)

    def _on_nav_click(self, index: int):
        if 0 <= index < self._stack.count():
            self._stack.setCurrentIndex(index)
            self._sidebar.set_active(index)
            # Refresh page data when navigating
            if index == 1:
                self._timeline_page.refresh_data()
            elif index == 2:
                self._apps_page.refresh_data()
            elif index == 3:
                self._insights_page.refresh_data()
            elif index == 5:
                self._reports_page.refresh_data()
            elif index == 6:
                self._settings_page.refresh_data()

    def _start_timers(self):
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._refresh_dashboard)
        self._refresh_timer.start(self._refresh_seconds * 1000)

        self._tick_timer = QTimer(self)
        self._tick_timer.timeout.connect(self._on_tick)
        self._tick_timer.start(1000)

    def _on_tick(self):
        if not self._tracking_paused:
            self._dashboard_page.tick_active_session()

    def _on_dashboard_date_changed(self, offset: int):
        self._selected_date += timedelta(days=offset)
        if self._selected_date > date.today():
            self._selected_date = date.today()
        self._refresh_dashboard()

    def _on_dashboard_reset_date(self):
        self._selected_date = date.today()
        self._refresh_dashboard()

    def _on_dashboard_stop_clicked(self):
        self._tracking_paused = not self._tracking_paused
        self._refresh_dashboard()

    def _refresh_dashboard(self):
        from trackora.utils.logging import log_info, log_error
        from dataclasses import replace
        log_info("dashboard refresh started")
        try:
            snapshot = self._repository.load_snapshot(self._selected_date)
            if self._tracking_paused:
                snapshot = replace(snapshot, active_app=None)
            self._dashboard_page.refresh(snapshot)
            
            if self._tracking_paused:
                self._dashboard_page._active_card._app_label.setText("Tracking Paused")
                self._dashboard_page._active_card._elapsed_label.setText("Paused")
                self._dashboard_page._active_card._stop_btn.set_paused(True)
                self._dashboard_page._active_card._category_badge.setVisible(False)
            else:
                self._dashboard_page._active_card._stop_btn.set_paused(False)

            if self._stack.currentIndex() == 1:
                self._timeline_page.refresh_data()
            elif self._stack.currentIndex() == 2:
                self._apps_page.refresh_data()
            elif self._stack.currentIndex() == 3:
                self._insights_page.refresh_data()
            elif self._stack.currentIndex() == 5:
                self._reports_page.refresh_data()
            elif self._stack.currentIndex() == 6:
                self._settings_page.refresh_data()
            log_info("dashboard refresh success")
        except Exception as exc:
            log_error(f"refresh exception if any: {exc}")

    def _apply_base_style(self):
        self.setStyleSheet(
            f"QMainWindow, QWidget {{ background: {_BG}; color: {_TEXT_PRIMARY}; "
            f"font-family: 'Inter', 'Cantarell', 'Segoe UI', sans-serif; }}"
        )
