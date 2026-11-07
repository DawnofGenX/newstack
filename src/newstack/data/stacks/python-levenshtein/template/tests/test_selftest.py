from __future__ import annotations

from {{ package_name }}.selftest import FIXTURE, Report, run


def test_the_report_counts_checks_and_failures_apart() -> None:
    report = Report()
    report.ok("a held claim", True)
    report.ok("a broken claim", False)
    report.equal("an equal pair", 1, 1)
    tail = report.render().splitlines()[-1]
    assert tail == "selftest: 2 checks passed, 1 failed"


def test_the_full_run_reports_no_failures() -> None:
    report = run()
    assert report.failed == 0
    assert report.checks > 40
    assert "selftest:" in report.render()


def test_the_fixture_marker_is_words_the_detector_can_find() -> None:
    assert FIXTURE == "a change costs one letter"
