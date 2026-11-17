"""Unit tests for the text-analysis helper."""

from __future__ import annotations

from {{ package_name }}.stats import analyze


def test_analyze_counts() -> None:
    result = analyze("hello world\n")
    assert result == {"text": "hello world\n", "lines": 1, "words": 2, "bytes": 12}


def test_analyze_empty() -> None:
    assert analyze("") == {"text": "", "lines": 0, "words": 0, "bytes": 0}