"""Unit tests for the worker."""

from __future__ import annotations

from {{ package_name }}.db import count_runs, reset_db
from {{ package_name }}.worker import run_ticks


def test_run_ticks() -> None:
    reset_db()
    result = run_ticks(2)
    assert result == 2
    assert count_runs() == 2