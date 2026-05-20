"""Reusable Qt widgets for Trackora.

Widget inventory
----------------
ActiveStatusCard  — live active-app session display (used by DashboardPage)
UsageTableWidget  — per-app usage table (used by DashboardPage)

Note: MetricCard is no longer exported from here — individual metric display
will be implemented directly in the redesigned DashboardPage.  The class
file is preserved at widgets/metric_card.py for reference until the redesign
integrates or supersedes it.
"""

from trackora.widgets.active_status_card import ActiveStatusCard
from trackora.widgets.usage_table import UsageTableWidget

__all__ = ["ActiveStatusCard", "UsageTableWidget"]
