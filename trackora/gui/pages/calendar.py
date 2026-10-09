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


