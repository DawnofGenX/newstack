from __future__ import annotations

from {{ package_name }}.selftest import (
    FIXTURE,
    Report,
    run,
)


def test_the_promises_answer_quiet() -> None:
    report = run()
    assert report.failed == 0, report.render()


def test_the_report_counts_its_own_checks() -> None:
    report = run()
    assert report.checks > 30
    assert report.render().endswith("failed")


def test_the_marker_lives_in_the_grower() -> None:
    assert FIXTURE in FIXTURE.lower()


def test_a_named_check_can_fail_loudly() -> None:
    report = Report()
    report.equal("a promise", 1, 2)
    assert report.failed == 1
    assert "1 != 2" in report.render()
