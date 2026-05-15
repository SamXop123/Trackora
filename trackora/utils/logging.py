"""Consistent console logging for the Trackora backend."""

from __future__ import annotations

import sys


def log_info(message: str) -> None:
    print(f"[Trackora] {message}", flush=True)


def log_warning(message: str) -> None:
    print(f"[Trackora] Warning: {message}", file=sys.stderr, flush=True)


def log_error(message: str) -> None:
    print(f"[Trackora] Error: {message}", file=sys.stderr, flush=True)
