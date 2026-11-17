"""The selftest, checked for shape."""

from __future__ import annotations

from {{ package_name }}.selftest import FIXTURE, run


def test_selftest_passes() -> None:
    report = run()
    assert report.failed == 0
    assert report.checks >= 10


def test_fixture_marker_present() -> None:
    assert FIXTURE == "selftest marker"
