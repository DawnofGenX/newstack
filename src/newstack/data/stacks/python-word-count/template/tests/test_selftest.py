"""The selftest, checked for shape."""

from __future__ import annotations

from {{ package_name }}.selftest import FIXTURE, run


def test_selftest_passes():
    report = run()
    assert report.failed == 0
    assert report.checks >= 10


def test_fixture_marker_present():
    assert FIXTURE == "a word count answers how many words a string holds"
