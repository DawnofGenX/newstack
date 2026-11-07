from __future__ import annotations

from {{ package_name }}.heap import (
    MinHeap,
)
from {{ package_name }}.selftest import (
    FIXTURE,
    run,
)


def test_the_selftest_reports_no_failures() -> None:
    report = run()
    assert report.failed == 0
    assert report.checks > 40
    assert "0 failed" in report.render()


def test_the_report_tail_counts_what_ran() -> None:
    report = run()
    tail = report.render().splitlines()[-1]
    assert tail == (
        f"selftest: {report.checks - report.failed} checks passed, {report.failed} failed"
    )


def test_the_detector_marker_lives_in_the_heap_docstring() -> None:
    assert FIXTURE in " ".join((MinHeap.__doc__ or "").split()).lower()
