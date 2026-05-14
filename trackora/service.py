"""
Poll the JSON file written by the Trackora Shell extension and print lines.

No Wayland, D-Bus window APIs, or AT-SPI in this process — the extension is the
single source of truth for focus.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from trackora.format_output import format_window_state_line
from trackora.window_state import load_window_state


def run_poll_loop(
    *,
    interval_sec: float,
    state_path: Path | None,
    stop_flag: list[bool] | None = None,
) -> None:
    """
    Read ``current_window.json`` every ``interval_sec`` and print one line.

    ``stop_flag`` is optional ``[False]``; set ``stop_flag[0] = True`` to exit
    after the current sleep slice (used by the CLI for SIGINT).
    """
    if interval_sec <= 0:
        raise ValueError("interval_sec must be positive")

    while stop_flag is None or not stop_flag[0]:
        state = load_window_state(state_path)
        if state is None:
            print(
                "[trackora] no valid window state (enable the Shell extension "
                "and wait for the first write)",
                file=sys.stderr,
                flush=True,
            )
        else:
            print(format_window_state_line(state), flush=True)

        remaining = float(interval_sec)
        step = min(0.2, remaining)
        while remaining > 0 and (stop_flag is None or not stop_flag[0]):
            time.sleep(step)
            remaining -= step
