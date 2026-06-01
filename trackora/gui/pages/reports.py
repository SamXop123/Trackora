"""Reports page — historical analytics and data export for Trackora."""
from __future__ import annotations
import csv, json, io
from datetime import date, timedelta
from PySide6.QtCore import Qt, QRectF, QSize, QDate
from PySide6.QtGui import (QBrush, QColor, QIcon, QLinearGradient, QPainter,
                            QPainterPath, QPen, QPixmap)
from PySide6.QtWidgets import (QDateEdit, QFileDialog, QFrame, QGraphicsDropShadowEffect,
                                QHBoxLayout, QLabel, QScrollArea, QSizePolicy,
                                QVBoxLayout, QWidget)
from trackora.database.dashboard import DashboardRepository
from trackora.models.dashboard import ReportsData, AppUsageSummary, DailyUsageSummary
from typing import TYPE_CHECKING

_BG = "#0d1117"; _CARD = "#141a23"; _CARD_LIGHTER = "#171f2a"
_CARD_BORDER = "#1c2735"; _TEXT_PRIMARY = "#e6edf5"
_TEXT_SECONDARY = "#8b9bb4"; _TEXT_MUTED = "#566a82"
_ACCENT = "#3b82f6"; _GREEN = "#34d399"

_CATEGORY_ICONS = {"Browsers":"🌐","Development":"💻","Music":"🎵",
    "Communication":"💬","System":"⚙️","Utilities":"📁","Other":"📦"}
_ICON_MAP = {"VS Code":["code","visual-studio-code"],"Chrome":["google-chrome"],
    "Brave":["brave-browser"],"Firefox":["firefox"],"Spotify":["spotify"],
    "Discord":["discord"],"Slack":["slack"],"Terminal":["utilities-terminal"],
    "Files":["org.gnome.Nautilus"],"Cursor":["co.anysphere.cursor"]}

def _get_icon(name, sz=20):
    for n in _ICON_MAP.get(name, [name.lower().replace(" ","-")]):
        ic = QIcon.fromTheme(n)
        if not ic.isNull(): return ic.pixmap(QSize(sz,sz))
    fb = QIcon.fromTheme("application-x-executable")
    return fb.pixmap(QSize(sz,sz)) if not fb.isNull() else None

def _shadow(w, blur=20, op=35, dy=3):
    s = QGraphicsDropShadowEffect(w); s.setBlurRadius(blur)
    s.setColor(QColor(0,0,0,op)); s.setOffset(0,dy); w.setGraphicsEffect(s)

def _fmt(secs):
    if secs < 60: return f"{secs}s"
    m = secs // 60
    if m < 60: return f"{m}m"
    h, rm = m // 60, m % 60
    return f"{h}h" if rm == 0 else f"{h}h {rm}m"


class _Card(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent); self.setObjectName("rptCard")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(self._css(_CARD)); _shadow(self)
    def _css(self, bg):
        return (f"QFrame#rptCard {{ background:{bg}; border:1px solid {_CARD_BORDER};"
                f" border-radius:14px; }}")
    def enterEvent(self, e): self.setStyleSheet(self._css(_CARD_LIGHTER))
    def leaveEvent(self, e): self.setStyleSheet(self._css(_CARD))


class _StatCard(_Card):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFixedHeight(110); self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lo = QVBoxLayout(self); lo.setContentsMargins(20,16,20,16); lo.setSpacing(4)
        h = QLabel(title.upper()); h.setStyleSheet(
            f"color:{_TEXT_MUTED};font-size:9px;font-weight:700;"
            f"letter-spacing:0.12em;background:transparent;border:none;")
        lo.addWidget(h)
        self._val = QLabel("—"); self._val.setStyleSheet(
            f"color:{_TEXT_PRIMARY};font-size:20px;font-weight:700;"
            f"background:transparent;border:none;")
        lo.addWidget(self._val)
        self._sub = QLabel(""); self._sub.setStyleSheet(
            f"color:{_TEXT_SECONDARY};font-size:11px;background:transparent;border:none;")
        lo.addWidget(self._sub)
    def set_val(self, v): self._val.setText(v)
    def set_sub(self, s): self._sub.setText(s)


class _FilterBtn(QWidget):
    def __init__(self, text, cb, parent=None):
        super().__init__(parent); self._active = False; self._text = text; self._cb = cb
        self.setCursor(Qt.CursorShape.PointingHandCursor); self.setFixedHeight(32)
        lo = QHBoxLayout(self); lo.setContentsMargins(14,0,14,0)
        self._lbl = QLabel(text); lo.addWidget(self._lbl); self._apply_style()
    def _apply_style(self):
        bg = _ACCENT if self._active else "transparent"
        fg = "#fff" if self._active else _TEXT_SECONDARY
        bd = f"1px solid {_ACCENT}" if self._active else f"1px solid {_CARD_BORDER}"
        self._lbl.setStyleSheet(f"color:{fg};font-size:12px;font-weight:600;"
            f"background:transparent;border:none;")
        self.setStyleSheet(f"background:{bg};border:{bd};border-radius:8px;")
    def set_active(self, a): self._active = a; self._apply_style()
    def mousePressEvent(self, e): self._cb(self._text)


class _TrendChart(QWidget):
    """Daily usage bar chart."""
    def __init__(self, parent=None):
        super().__init__(parent); self._data = []; self.setMinimumHeight(200)
    def set_data(self, days: list[DailyUsageSummary]):
        self._data = days; self.update()
    def paintEvent(self, e):
        if not self._data: return
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pad_l, pad_r, pad_t, pad_b = 10, 10, 10, 28
        cw = w - pad_l - pad_r; ch = h - pad_t - pad_b
        n = len(self._data); mx = max((d.duration_seconds for d in self._data), default=1) or 1
        peak_i = max(range(n), key=lambda i: self._data[i].duration_seconds)
        bw = max(min(cw // n - 4, 28), 6); gap = (cw - bw * n) / max(n, 1)
        for i, d in enumerate(self._data):
            bx = pad_l + int(i * (bw + gap) + gap / 2)
            bh = max(int((d.duration_seconds / mx) * ch), 2)
            by = pad_t + ch - bh; r = QRectF(bx, by, bw, bh)
            g = QLinearGradient(r.topLeft(), r.bottomLeft())
            if i == peak_i:
                g.setColorAt(0, QColor("#60a5fa")); g.setColorAt(1, QColor("#3b82f6"))
            else:
                g.setColorAt(0, QColor(59,130,246,120)); g.setColorAt(1, QColor(59,130,246,70))
            path = QPainterPath(); path.addRoundedRect(r, 3, 3)
            p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen); p.drawPath(path)
            # Label
            lbl = d.label.replace("\n"," ")
            if n <= 14 or i % max(n//10,1) == 0:
                p.setPen(QPen(QColor(_TEXT_MUTED)))
                p.drawText(QRectF(bx-6, h-pad_b+4, bw+12, 16), Qt.AlignmentFlag.AlignCenter, lbl)
        p.end()


class _AppTableRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setFixedHeight(42)
        self._hovered = False
        lo = QHBoxLayout(self); lo.setContentsMargins(16,0,16,0); lo.setSpacing(12)
        self._icon = QLabel(); self._icon.setFixedSize(20,20)
        lo.addWidget(self._icon)
        self._name = QLabel(); self._name.setStyleSheet(
            f"color:{_TEXT_PRIMARY};font-size:13px;font-weight:500;background:transparent;border:none;")
        lo.addWidget(self._name, 1)
        self._dur = QLabel(); self._dur.setStyleSheet(
            f"color:{_TEXT_SECONDARY};font-size:12px;font-weight:600;background:transparent;border:none;")
        self._dur.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        lo.addWidget(self._dur)
        self._pct = QLabel(); self._pct.setFixedWidth(55)
        self._pct.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        self._pct.setStyleSheet(
            f"color:{_ACCENT};font-size:12px;font-weight:700;background:transparent;border:none;")
        lo.addWidget(self._pct)
    def set_data(self, name, dur, pct):
        self._name.setText(name); self._dur.setText(_fmt(dur)); self._pct.setText(f"{pct}%")
        px = _get_icon(name, 20)
        if px: self._icon.setPixmap(px)
    def enterEvent(self, e):
        self.setStyleSheet(f"background:{_CARD_LIGHTER};border-radius:8px;")
    def leaveEvent(self, e):
        self.setStyleSheet("background:transparent;")


class _CategoryRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); self.setFixedHeight(38)
        lo = QHBoxLayout(self); lo.setContentsMargins(16,0,16,0); lo.setSpacing(10)
        self._icon = QLabel(); self._icon.setStyleSheet(
            "font-family:'Noto Color Emoji','Segoe UI Emoji',sans-serif;"
            "font-size:14px;background:transparent;border:none;")
        self._icon.setFixedWidth(22); lo.addWidget(self._icon)
        self._name = QLabel(); self._name.setStyleSheet(
            f"color:{_TEXT_PRIMARY};font-size:13px;font-weight:500;background:transparent;border:none;")
        lo.addWidget(self._name, 1)
        self._dur = QLabel(); self._dur.setStyleSheet(
            f"color:{_TEXT_SECONDARY};font-size:12px;font-weight:600;background:transparent;border:none;")
        self._dur.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter); lo.addWidget(self._dur)
        self._pct = QLabel(); self._pct.setFixedWidth(55)
        self._pct.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
        self._pct.setStyleSheet(
            f"color:{_ACCENT};font-size:12px;font-weight:700;background:transparent;border:none;")
        lo.addWidget(self._pct)
    def set_data(self, cat, dur, pct):
        self._icon.setText(_CATEGORY_ICONS.get(cat,"📦"))
        self._name.setText(cat); self._dur.setText(_fmt(dur)); self._pct.setText(f"{pct}%")
    def enterEvent(self, e):
        self.setStyleSheet(f"background:{_CARD_LIGHTER};border-radius:8px;")
    def leaveEvent(self, e):
        self.setStyleSheet("background:transparent;")


class _ExportBtn(QWidget):
    def __init__(self, text, cb, parent=None):
        super().__init__(parent); self._cb = cb; self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(130, 36)
        lo = QHBoxLayout(self); lo.setContentsMargins(0,0,0,0)
        lbl = QLabel(text); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"color:#fff;font-size:12px;font-weight:600;"
            f"background:transparent;border:none;")
        lo.addWidget(lbl)
        self.setStyleSheet(f"background:{_ACCENT};border-radius:8px;")
    def mousePressEvent(self, e): self._cb()
    def enterEvent(self, e): self.setStyleSheet("background:#2563eb;border-radius:8px;")
    def leaveEvent(self, e): self.setStyleSheet(f"background:{_ACCENT};border-radius:8px;")


# ═══════════════════════════════════════════════════════════════════════════
#  REPORTS PAGE
# ═══════════════════════════════════════════════════════════════════════════

class ReportsPage(QWidget):
    _RANGES = {"Today":1,"Yesterday":None,"Last 7 Days":7,"Last 30 Days":30}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._repository = None; self._active_range = "Last 7 Days"
        self._last_data: ReportsData | None = None

        scroll = QScrollArea(self); scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea{{background:{_BG};border:none;}}"
            f"QScrollBar:vertical{{background:{_BG};width:5px;}}"
            f"QScrollBar::handle:vertical{{background:{_CARD_BORDER};border-radius:2px;min-height:30px;}}"
            f"QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}")
        ctr = QWidget(); ctr.setStyleSheet(f"background:{_BG};")
        scroll.setWidget(ctr)
        pg = QVBoxLayout(self); pg.setContentsMargins(0,0,0,0); pg.addWidget(scroll)
        main = QVBoxLayout(ctr); main.setContentsMargins(28,14,28,28); main.setSpacing(16)

        # Header
        hdr = QVBoxLayout(); hdr.setSpacing(4)
        t = QLabel("Reports"); t.setStyleSheet(
            f"color:{_TEXT_PRIMARY};font-size:22px;font-weight:700;background:transparent;border:none;")
        hdr.addWidget(t)
        st = QLabel("Analyze and export your activity history"); st.setStyleSheet(
            f"color:{_TEXT_SECONDARY};font-size:13px;background:transparent;border:none;")
        hdr.addWidget(st); main.addLayout(hdr)

        # Filters
        filt = QHBoxLayout(); filt.setSpacing(8)
        self._filter_btns = {}
        for name in ["Today","Yesterday","Last 7 Days","Last 30 Days","Custom Range"]:
            btn = _FilterBtn(name, self._on_filter)
            self._filter_btns[name] = btn; filt.addWidget(btn)
        filt.addStretch(1); main.addLayout(filt)
        self._filter_btns["Last 7 Days"].set_active(True)

        # Date Pickers directly below the filter row
        self._custom_range_widget = QWidget()
        self._custom_range_widget.setVisible(False)
        self._custom_range_widget.setStyleSheet("background:transparent;border:none;")
        cw_lo = QHBoxLayout(self._custom_range_widget)
        cw_lo.setContentsMargins(0, 4, 0, 8)
        cw_lo.setSpacing(12)

        start_lbl = QLabel("Start Date:")
        start_lbl.setStyleSheet(f"color:{_TEXT_SECONDARY};font-size:12px;font-weight:600;background:transparent;")
        cw_lo.addWidget(start_lbl)

        self._start_date_edit = QDateEdit()
        self._start_date_edit.setCalendarPopup(True)
        self._start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self._start_date_edit.setStyleSheet(self._get_date_picker_qss())
        cw_lo.addWidget(self._start_date_edit)

        end_lbl = QLabel("End Date:")
        end_lbl.setStyleSheet(f"color:{_TEXT_SECONDARY};font-size:12px;font-weight:600;background:transparent;")
        cw_lo.addWidget(end_lbl)

        self._end_date_edit = QDateEdit()
        self._end_date_edit.setCalendarPopup(True)
        self._end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self._end_date_edit.setStyleSheet(self._get_date_picker_qss())
        cw_lo.addWidget(self._end_date_edit)

        # Setup default date values (start = today - 7 days, end = today)
        today = date.today()
        end_q = QDate(today.year, today.month, today.day)
        start_dt = today - timedelta(days=7)
        start_q = QDate(start_dt.year, start_dt.month, start_dt.day)
        self._start_date_edit.setDate(start_q)
        self._end_date_edit.setDate(end_q)

        self._start_date_edit.dateChanged.connect(self._on_custom_date_changed)
        self._end_date_edit.dateChanged.connect(self._on_custom_date_changed)

        cw_lo.addStretch(1)
        main.addWidget(self._custom_range_widget)

        # Summary cards
        r1 = QHBoxLayout(); r1.setSpacing(16)
        self._s_time = _StatCard("Total Screen Time")
        self._s_sess = _StatCard("Total Sessions")
        self._s_app = _StatCard("Most Used App")
        self._s_day = _StatCard("Most Active Day")
        r1.addWidget(self._s_time); r1.addWidget(self._s_sess)
        r1.addWidget(self._s_app); r1.addWidget(self._s_day)
        main.addLayout(r1)

        # Trend chart
        self._trend_card = _Card()
        tc_lo = QVBoxLayout(self._trend_card)
        tc_lo.setContentsMargins(24,20,24,20); tc_lo.setSpacing(4)
        tc_t = QLabel("USAGE TREND"); tc_t.setStyleSheet(
            f"color:{_TEXT_MUTED};font-size:10px;font-weight:700;"
            f"letter-spacing:0.12em;background:transparent;border:none;")
        tc_lo.addWidget(tc_t)
        self._trend_sub = QLabel("Daily activity across selected range")
        self._trend_sub.setStyleSheet(
            f"color:{_TEXT_MUTED};font-size:11px;background:transparent;border:none;")
        tc_lo.addWidget(self._trend_sub)
        tc_lo.addSpacing(6)
        self._trend_chart = _TrendChart(); tc_lo.addWidget(self._trend_chart)
        main.addWidget(self._trend_card)

        # Row: Apps table + Categories
        r3 = QHBoxLayout(); r3.setSpacing(16)

        # Apps table
        self._apps_card = _Card()
        ac_lo = QVBoxLayout(self._apps_card)
        ac_lo.setContentsMargins(24,20,24,16); ac_lo.setSpacing(4)
        ac_t = QLabel("TOP APPLICATIONS"); ac_t.setStyleSheet(
            f"color:{_TEXT_MUTED};font-size:10px;font-weight:700;"
            f"letter-spacing:0.12em;background:transparent;border:none;")
        ac_lo.addWidget(ac_t)
        ac_s = QLabel("Sorted by usage time"); ac_s.setStyleSheet(
            f"color:{_TEXT_MUTED};font-size:11px;background:transparent;border:none;")
        ac_lo.addWidget(ac_s); ac_lo.addSpacing(6)
        # Table header
        th = QWidget(); th.setFixedHeight(28)
        th_lo = QHBoxLayout(th); th_lo.setContentsMargins(16,0,16,0); th_lo.setSpacing(12)
        
        icon_spacer = QLabel()
        icon_spacer.setFixedWidth(20)
        th_lo.addWidget(icon_spacer)
        
        for txt, stretch, w in [("App",1,0),("Duration",0,0),("",0,55)]:
            l = QLabel(txt)
            l.setStyleSheet(
                f"color:{_TEXT_MUTED};font-size:9px;font-weight:700;"
                f"letter-spacing:0.1em;background:transparent;border:none;"
            )
            if w:
                l.setFixedWidth(w)
                l.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)
            th_lo.addWidget(l, stretch)
        ac_lo.addWidget(th)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFixedHeight(1); sep.setStyleSheet(f"background:{_CARD_BORDER};border:none;")
        ac_lo.addWidget(sep)
        self._app_rows_lo = QVBoxLayout(); self._app_rows_lo.setSpacing(2)
        ac_lo.addLayout(self._app_rows_lo); ac_lo.addStretch(1)

        # Categories
        self._cat_card = _Card()
        cc_lo = QVBoxLayout(self._cat_card)
        cc_lo.setContentsMargins(24,20,24,16); cc_lo.setSpacing(4)
        cc_t = QLabel("CATEGORY BREAKDOWN"); cc_t.setStyleSheet(
            f"color:{_TEXT_MUTED};font-size:10px;font-weight:700;"
            f"letter-spacing:0.12em;background:transparent;border:none;")
        cc_lo.addWidget(cc_t)
        cc_s = QLabel("Usage by application category"); cc_s.setStyleSheet(
            f"color:{_TEXT_MUTED};font-size:11px;background:transparent;border:none;")
        cc_lo.addWidget(cc_s); cc_lo.addSpacing(6)
        self._cat_rows_lo = QVBoxLayout(); self._cat_rows_lo.setSpacing(2)
        cc_lo.addLayout(self._cat_rows_lo); cc_lo.addStretch(1)

        r3.addWidget(self._apps_card, 3); r3.addWidget(self._cat_card, 2)
        main.addLayout(r3)

        # Export section
        self._export_card = _Card()
        ex_lo = QVBoxLayout(self._export_card)
        ex_lo.setContentsMargins(24,20,24,20); ex_lo.setSpacing(8)
        ex_t = QLabel("EXPORT REPORT"); ex_t.setStyleSheet(
            f"color:{_TEXT_MUTED};font-size:10px;font-weight:700;"
            f"letter-spacing:0.12em;background:transparent;border:none;")
        ex_lo.addWidget(ex_t)
        ex_s = QLabel("Download your activity data for the selected date range")
        ex_s.setStyleSheet(f"color:{_TEXT_MUTED};font-size:11px;background:transparent;border:none;")
        ex_lo.addWidget(ex_s); ex_lo.addSpacing(4)
        btn_row = QHBoxLayout(); btn_row.setSpacing(12)
        btn_row.addWidget(_ExportBtn("⬇  Export CSV", self._export_csv))
        btn_row.addWidget(_ExportBtn("⬇  Export JSON", self._export_json))
        btn_row.addStretch(1); ex_lo.addLayout(btn_row)
        main.addWidget(self._export_card)

        # Empty state
        self._empty = QWidget(); el = QVBoxLayout(self._empty)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter); el.setContentsMargins(0,60,0,60); el.setSpacing(10)
        ei = QLabel("◷"); ei.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ei.setStyleSheet(f"color:{_TEXT_MUTED};font-size:40px;background:transparent;border:none;")
        el.addWidget(ei)
        et = QLabel("No activity data for this period"); et.setAlignment(Qt.AlignmentFlag.AlignCenter)
        et.setStyleSheet(f"color:{_TEXT_SECONDARY};font-size:15px;font-weight:500;"
            f"background:transparent;border:none;")
        el.addWidget(et)
        es = QLabel("Try selecting a different date range"); es.setAlignment(Qt.AlignmentFlag.AlignCenter)
        es.setStyleSheet(f"color:{_TEXT_MUTED};font-size:12px;background:transparent;border:none;")
        el.addWidget(es)
        self._empty.setVisible(False); main.addWidget(self._empty)
        main.addStretch(1)

        self._content_widgets = [self._s_time, self._s_sess, self._s_app, self._s_day,
            self._trend_card, self._apps_card, self._cat_card, self._export_card]

    def set_repository(self, repo): self._repository = repo

    def refresh_data(self):
        if not self._repository: return
        rng = self._active_range
        today = date.today()
        if rng == "Today":
            data = self._repository.load_reports_data(days=1)
        elif rng == "Yesterday":
            y = today - timedelta(days=1)
            data = self._repository.load_reports_data(start_date=y, end_date=y)
        elif rng == "Last 7 Days":
            data = self._repository.load_reports_data(days=7)
        elif rng == "Last 30 Days":
            data = self._repository.load_reports_data(days=30)
        elif rng == "Custom Range":
            sq = self._start_date_edit.date()
            eq = self._end_date_edit.date()
            start_dt = date(sq.year(), sq.month(), sq.day())
            end_dt = date(eq.year(), eq.month(), eq.day())
            data = self._repository.load_reports_data(start_date=start_dt, end_date=end_dt)
        else:
            data = self._repository.load_reports_data(days=7)
        self._last_data = data
        if not data or data.total_screen_time_seconds == 0:
            for w in self._content_widgets: w.setVisible(False)
            self._empty.setVisible(True); return
        self._empty.setVisible(False)
        for w in self._content_widgets: w.setVisible(True)
        self._s_time.set_val(_fmt(data.total_screen_time_seconds))
        self._s_time.set_sub(f"across {len(data.daily_usage)} day{'s' if len(data.daily_usage)!=1 else ''}")
        self._s_sess.set_val(str(data.total_sessions))
        avg = data.total_screen_time_seconds // max(data.total_sessions,1)
        self._s_sess.set_sub(f"avg {_fmt(avg)} per session")
        self._s_app.set_val(data.most_used_app_name)
        self._s_app.set_sub(_fmt(data.most_used_app_duration))
        self._s_day.set_val(data.most_active_day_label)
        self._s_day.set_sub(_fmt(data.most_active_day_seconds))
        self._trend_chart.set_data(data.daily_usage)
        # Apps
        while self._app_rows_lo.count():
            it = self._app_rows_lo.takeAt(0)
            if it is not None:
                w = it.widget()
                if w: w.deleteLater()
        total = sum(a.duration_seconds for a in data.app_usage) or 1
        for app in data.app_usage[:10]:
            pct = int((app.duration_seconds / total) * 100)
            row = _AppTableRow(); row.set_data(app.app_name, app.duration_seconds, pct)
            self._app_rows_lo.addWidget(row)
        # Categories
        while self._cat_rows_lo.count():
            it = self._cat_rows_lo.takeAt(0)
            if it is not None:
                w = it.widget()
                if w: w.deleteLater()
        for cat, dur, pct in data.category_breakdown:
            row = _CategoryRow(); row.set_data(cat, dur, pct)
            self._cat_rows_lo.addWidget(row)

    def _on_filter(self, name):
        self._active_range = name
        for k, b in self._filter_btns.items(): b.set_active(k == name)
        self._custom_range_widget.setVisible(name == "Custom Range")
        self.refresh_data()

    def _on_custom_date_changed(self):
        if self._active_range == "Custom Range":
            start = self._start_date_edit.date()
            end = self._end_date_edit.date()
            if start > end:
                # Dynamic auto-adjust bounds for seamless UX
                self._end_date_edit.setDate(start)
            self.refresh_data()

    def _get_date_picker_qss(self) -> str:
        return f"""
            QDateEdit {{
                background: {_CARD};
                border: 1px solid {_CARD_BORDER};
                border-radius: 8px;
                color: {_TEXT_PRIMARY};
                font-size: 12px;
                font-weight: 600;
                padding: 6px 12px;
                min-width: 110px;
            }}
            QDateEdit::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 26px;
                border-left: 1px solid {_CARD_BORDER};
                background: {_CARD_LIGHTER};
                border-top-right-radius: 7px;
                border-bottom-right-radius: 7px;
            }}
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
        """

    def _export_csv(self):
        if not self._last_data: return
        path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "trackora_report.csv", "CSV (*.csv)")
        if not path: return
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            rng_header = f"Custom Range ({self._start_date_edit.date().toString('yyyy-MM-dd')} to {self._end_date_edit.date().toString('yyyy-MM-dd')})" if self._active_range == "Custom Range" else self._active_range
            w.writerow([f"Trackora Telemetry Report - {rng_header}"])
            w.writerow([])
            w.writerow(["App","Duration (seconds)","Duration"])
            for a in self._last_data.app_usage:
                w.writerow([a.app_name, a.duration_seconds, _fmt(a.duration_seconds)])
            w.writerow([]); w.writerow(["Date","Duration (seconds)","Duration"])
            for d in self._last_data.daily_usage:
                w.writerow([d.day.isoformat(), d.duration_seconds, _fmt(d.duration_seconds)])

    def _export_json(self):
        if not self._last_data: return
        path, _ = QFileDialog.getSaveFileName(self, "Export JSON", "trackora_report.json", "JSON (*.json)")
        if not path: return
        rng_name = f"Custom Range ({self._start_date_edit.date().toString('yyyy-MM-dd')} to {self._end_date_edit.date().toString('yyyy-MM-dd')})" if self._active_range == "Custom Range" else self._active_range
        obj = {"range": rng_name,
            "total_screen_time_seconds": self._last_data.total_screen_time_seconds,
            "total_sessions": self._last_data.total_sessions,
            "apps": [{"name":a.app_name,"seconds":a.duration_seconds}
                     for a in self._last_data.app_usage],
            "daily": [{"date":d.day.isoformat(),"seconds":d.duration_seconds}
                      for d in self._last_data.daily_usage],
            "categories": [{"name":c,"seconds":d,"pct":p}
                           for c,d,p in self._last_data.category_breakdown]}
        with open(path, "w") as f: json.dump(obj, f, indent=2)
