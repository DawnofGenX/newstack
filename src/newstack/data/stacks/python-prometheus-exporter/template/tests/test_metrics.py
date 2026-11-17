"""Unit tests for metric rendering."""

from __future__ import annotations

from {{ package_name }}.metrics import render_metrics


def test_render_contains_help() -> None:
    body = render_metrics()
    assert b"# HELP app_up" in body
    assert b"app_up 1" in body