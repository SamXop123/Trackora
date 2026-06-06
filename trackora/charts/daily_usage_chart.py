"""Custom-painted daily usage hourly bar chart widget.

Draws rounded capsule bars, grid lines, and labels to match the premium reference image.
"""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QLinearGradient, QPen, QBrush
from PySide6.QtWidgets import QWidget, QSizePolicy

# ── Text & Theme Colors matching the theme ──────────────────────────────────
_TEXT_PRIMARY = "#e6edf5"
_TEXT_SECONDARY = "#8b9bb4"
_TEXT_MUTED = "#566a82"
_ACCENT = "#3b82f6"


class DailyUsageChart(QWidget):
    """Custom-painted daily usage hourly bar chart widget.
    
    Draws rounded capsule bars, grid lines, and labels to match the premium reference image.
    """
    
    _PAD_LEFT = 35      # space for left axis (0m, 15m, 30m...)
    _PAD_RIGHT = 15
    _PAD_TOP = 15       # space at the top of the chart
    _PAD_BOTTOM = 22    # space for bottom hour labels
    _BAR_GAP_RATIO = 0.25 # gap between bars
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._values: list[float] = [0.0] * 24
        self._hovered_index: int = -1
        self.setMinimumHeight(190)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def update_chart(self, hour_labels: list[str], hour_values: list[float]) -> None:
        # hour_values are in hours (e.g. 0.5 = 30m). Let's cap values to 1.0 (60m).
        self._values = [max(0.0, float(v)) for v in hour_values]
        # Pad to 24 if shorter
        while len(self._values) < 24:
            self._values.append(0.0)
        self.update()

    def _bar_rects(self) -> list[QRectF]:
        if not self._values:
            return []
        n = len(self._values)
        usable_w = self.width() - self._PAD_LEFT - self._PAD_RIGHT
        usable_h = self.height() - self._PAD_TOP - self._PAD_BOTTOM
        slot_w = usable_w / n
        gap = slot_w * self._BAR_GAP_RATIO
        bar_w = slot_w - gap
        
        # Max value on y-axis is 1.0 (60 minutes)
        max_val = 1.0
        
        rects = []
        for i, val in enumerate(self._values):
            ratio = min(val / max_val, 1.0)
            bar_h = ratio * usable_h
            x = self._PAD_LEFT + i * slot_w + gap / 2
            y = self._PAD_TOP + usable_h - bar_h
            rects.append(QRectF(x, y, bar_w, bar_h))
        return rects

    def mouseMoveEvent(self, event):
        rects = self._bar_rects()
        new_idx = -1
        for i, r in enumerate(rects):
            check_rect = QRectF(r.x() - 1, self._PAD_TOP, r.width() + 2, self.height() - self._PAD_TOP - self._PAD_BOTTOM)
            if check_rect.contains(event.position()):
                new_idx = i
                break
        if new_idx != self._hovered_index:
            self._hovered_index = new_idx
            self.update()

    def leaveEvent(self, event):
        self._hovered_index = -1
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(720, 280)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        usable_w = w - self._PAD_LEFT - self._PAD_RIGHT
        usable_h = h - self._PAD_TOP - self._PAD_BOTTOM
        
        # ── Draw horizontal grid lines and left labels ──────────────────
        grid_vals = [0.0, 0.25, 0.5, 0.75, 1.0] # 0m, 15m, 30m, 45m, 60m
        grid_labels = ["0m", "15m", "30m", "45m", "60m"]
        
        grid_font = QFont("Inter", 8)
        painter.setFont(grid_font)
        
        for val, label in zip(grid_vals, grid_labels):
            y = self._PAD_TOP + usable_h - (val * usable_h)
            
            # Draw grid line (very subtle)
            painter.setPen(QPen(QColor(255, 255, 255, 8), 1, Qt.DashLine if val > 0 else Qt.SolidLine))
            painter.drawLine(self._PAD_LEFT, y, w - self._PAD_RIGHT, y)
            
            # Draw left label
            painter.setPen(QPen(QColor(_TEXT_MUTED)))
            label_rect = QRectF(5, y - 6, self._PAD_LEFT - 10, 12)
            painter.drawText(label_rect, Qt.AlignRight | Qt.AlignVCenter, label)
            
        # ── Draw bars and x-axis labels ─────────────────────────────────
        rects = self._bar_rects()
        hour_labels = [
            "12 AM", "", "", "3 AM", "", "", "6 AM", "", "",
            "9 AM", "", "", "12 PM", "", "", "3 PM", "", "",
            "6 PM", "", "", "9 PM", "", "",
        ]
        
        n = len(self._values)
        slot_w = usable_w / n
        
        for i, (rect, val) in enumerate(zip(rects, self._values)):
            is_hovered = (i == self._hovered_index)
            
            # If bar has no value, draw a tiny 2px dot at the baseline
            if val <= 0.001:
                painter.setBrush(QBrush(QColor(59, 130, 246, 30)))
                painter.setPen(Qt.NoPen)
                dot_y = self._PAD_TOP + usable_h - 2
                painter.drawRoundedRect(QRectF(rect.x(), dot_y, rect.width(), 2), 1, 1)
            else:
                # Rounded capsule bar with blue gradient
                bar_grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                if is_hovered:
                    # Hover highlight: brighter gradient
                    bar_grad.setColorAt(0, QColor("#60a5fa"))
                    bar_grad.setColorAt(1, QColor("#2563eb"))
                else:
                    bar_grad.setColorAt(0, QColor("#3b82f6"))
                    bar_grad.setColorAt(1, QColor("#1d4ed8"))
                    
                rad = rect.width() / 2
                painter.setBrush(QBrush(bar_grad))
                
                if is_hovered:
                    painter.setPen(QPen(QColor("#93c5fd"), 1))
                else:
                    painter.setPen(Qt.NoPen)
                    
                painter.drawRoundedRect(rect, rad, rad)
                
            # Draw bottom label if present
            lbl = hour_labels[i]
            if lbl:
                painter.setFont(grid_font)
                painter.setPen(QPen(QColor(_TEXT_MUTED)))
                lbl_x = self._PAD_LEFT + i * slot_w
                lbl_rect = QRectF(lbl_x - 10, h - self._PAD_BOTTOM + 4, slot_w + 20, 16)
                painter.drawText(lbl_rect, Qt.AlignCenter, lbl)
                
        # ── Draw hover value tooltip above hovered bar ─────────────────
        if self._hovered_index != -1 and self._values[self._hovered_index] > 0:
            val = self._values[self._hovered_index]
            mins = int(val * 60)
            rect = rects[self._hovered_index]
            
            # Tooltip text
            tip_text = f"{mins}m"
            painter.setFont(QFont("Inter", 8, QFont.Bold))
            
            # Draw tooltip bubble
            metrics = painter.fontMetrics()
            tw = metrics.horizontalAdvance(tip_text) + 8
            th = metrics.height() + 4
            tx = rect.center().x() - tw / 2
            ty = rect.y() - th - 6
            
            painter.setBrush(QBrush(QColor(15, 23, 42)))
            painter.setPen(QPen(QColor(59, 130, 246), 1))
            painter.drawRoundedRect(QRectF(tx, ty, tw, th), 4, 4)
            
            painter.setPen(QPen(QColor("#ffffff")))
            painter.drawText(QRectF(tx, ty, tw, th), Qt.AlignCenter, tip_text)
            
        painter.end()
