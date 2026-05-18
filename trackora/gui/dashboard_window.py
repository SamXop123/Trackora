"""Main dashboard window for the Trackora desktop application."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from trackora.charts import DailyUsageChart
from trackora.database.dashboard import DashboardRepository
from trackora.models.dashboard import DashboardSnapshot
from trackora.utils.formatting import format_duration_compact, format_last_refreshed
from trackora.widgets.active_status_card import ActiveStatusCard
from trackora.widgets.metric_card import MetricCard
from trackora.widgets.usage_table import UsageTableWidget


class DashboardWindow(QMainWindow):
    """Main Trackora dashboard UI."""

    def __init__(self, *, database_path: Path, refresh_seconds: int) -> None:
        super().__init__()
        self._repository = DashboardRepository(database_path)
        self._refresh_seconds = refresh_seconds
        self.setWindowTitle("Trackora Dashboard")
        self.resize(1220, 820)
        self.setMinimumSize(1040, 700)
        self._build_ui()
        self._apply_styles()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh_dashboard)
        self._timer.start(self._refresh_seconds * 1000)
        self._active_tick_timer = QTimer(self)
        self._active_tick_timer.timeout.connect(self._active_status_card.tick)
        self._active_tick_timer.start(1000)
        self.refresh_dashboard()

    def _build_ui(self) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(28, 24, 28, 24)
        outer.setSpacing(18)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)
        title_block = QVBoxLayout()
        title_block.setSpacing(4)

        title = QLabel("Trackora")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("Wayland-native activity dashboard for your current day")
        subtitle.setObjectName("subtitleLabel")

        title_block.addWidget(title)
        title_block.addWidget(subtitle)
        header_layout.addLayout(title_block)
        header_layout.addStretch(1)

        self._status_label = QLabel("Waiting for data…")
        self._status_label.setObjectName("statusLabel")
        header_layout.addWidget(self._status_label)

        outer.addLayout(header_layout)

        metrics_layout = QGridLayout()
        metrics_layout.setHorizontalSpacing(16)
        metrics_layout.setVerticalSpacing(16)

        self._total_today_card = MetricCard(
            title="Total Screen Time Today",
            value="0m",
            subtitle="Across all tracked apps",
        )
        self._top_app_card = MetricCard(
            title="Top App Today",
            value="No data",
            subtitle="No usage recorded yet",
        )
        self._refresh_card = MetricCard(
            title="Last Refresh",
            value="Waiting…",
            subtitle="Dashboard auto-refresh",
        )
        self._active_status_card = ActiveStatusCard()

        metrics_layout.addWidget(self._total_today_card, 0, 0)
        metrics_layout.addWidget(self._top_app_card, 0, 1)
        metrics_layout.addWidget(self._refresh_card, 0, 2)
        metrics_layout.addWidget(self._active_status_card, 1, 0, 1, 3)
        outer.addLayout(metrics_layout)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(18)

        self._chart = DailyUsageChart()
        self._chart_section = self._wrap_section("Today's Usage Chart", self._chart)
        self._chart_section.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        left_layout.addWidget(self._chart_section, 3)

        self._usage_table = UsageTableWidget()
        self._table_section = self._wrap_section("Top Apps Today", self._usage_table)
        left_layout.addWidget(self._table_section, 2)
        left_layout.setStretch(0, 3)
        left_layout.setStretch(1, 2)
        content_layout.addWidget(left_panel, 3)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(18)

        self._top_apps_summary = QLabel("No tracked apps yet.")
        self._top_apps_summary.setObjectName("summaryLabel")
        self._top_apps_summary.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._top_apps_summary.setWordWrap(True)

        right_layout.addWidget(self._wrap_section("Today's Leaders", self._top_apps_summary))
        right_layout.addStretch(1)
        content_layout.addWidget(right_panel, 2)

        outer.addLayout(content_layout)

    def _wrap_section(self, title: str, widget: QWidget) -> QWidget:
        container = QWidget()
        container.setObjectName("sectionCard")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
        layout.addWidget(widget, 1)
        return container

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #0b0e12;
                color: #f3f7ff;
            }
            QLabel#subtitleLabel {
                color: #8ea1bd;
                font-size: 13px;
            }
            QLabel#statusLabel {
                background: #111821;
                border: 1px solid #1d2a39;
                border-radius: 10px;
                color: #a9bdd8;
                padding: 10px 14px;
                font-size: 12px;
            }
            QWidget#metricCard, QWidget#sectionCard {
                background: #111418;
                border: 1px solid #1c2430;
                border-radius: 18px;
            }
            QLabel#sectionTitle {
                color: #f3f7ff;
                font-size: 15px;
                font-weight: 600;
            }
            QLabel#summaryLabel {
                color: #d6ddea;
                font-size: 14px;
                line-height: 1.5;
            }
            QTableWidget {
                background: transparent;
                border: none;
                gridline-color: #1c2430;
                color: #f3f7ff;
                selection-background-color: #1e395f;
                selection-color: #f3f7ff;
            }
            QHeaderView::section {
                background: #0f1620;
                color: #8ea1bd;
                border: none;
                padding: 8px;
                font-weight: 600;
            }
            QTableCornerButton::section {
                background: #0f1620;
                border: none;
            }
            """
        )

    def refresh_dashboard(self) -> None:
        snapshot = self._repository.load_snapshot()
        self._render_snapshot(snapshot)

    def _render_snapshot(self, snapshot: DashboardSnapshot) -> None:
        self._status_label.setText(snapshot.status_message)
        self._total_today_card.set_content(
            value=format_duration_compact(snapshot.total_today_seconds),
            subtitle=f"{len(snapshot.all_apps)} apps tracked today",
        )

        if snapshot.top_apps:
            leader = snapshot.top_apps[0]
            self._top_app_card.set_content(
                value=leader.app_name,
                subtitle=format_duration_compact(leader.duration_seconds),
            )
        else:
            self._top_app_card.set_content(
                value="No data",
                subtitle="Open a few apps to start seeing usage",
            )

        self._refresh_card.set_content(
            value=format_last_refreshed(snapshot.last_refreshed),
            subtitle=f"Auto-refresh every {self._refresh_seconds}s",
        )
        self._active_status_card.update_status(snapshot.active_app)
        self._usage_table.set_rows(snapshot.all_apps)
        self._chart.update_chart(snapshot.hourly_labels, snapshot.hourly_values)
        self._top_apps_summary.setText(self._build_summary_text(snapshot))

    def _build_summary_text(self, snapshot: DashboardSnapshot) -> str:
        if not snapshot.top_apps:
            return "No tracked app sessions yet today. Once the background tracker records activity, your leaders will appear here."

        lines = []
        for index, item in enumerate(snapshot.top_apps[:3], start=1):
            lines.append(
                f"{index}. {item.app_name}  •  {format_duration_compact(item.duration_seconds)}"
            )

        if snapshot.active_app is not None:
            lines.append("")
            lines.append(
                "Active now: "
                f"{snapshot.active_app.app_name}  •  "
                f"{format_duration_compact(snapshot.active_app.elapsed_seconds)}"
            )

        return "\n".join(lines)
