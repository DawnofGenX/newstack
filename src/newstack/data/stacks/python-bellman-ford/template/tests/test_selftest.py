from __future__ import annotations

from {{ package_name }} import walk as walk_module
from {{ package_name }}.selftest import (
    FIXTURE,
    Report,
    run,
)


def test_the_run_makes_no_failures() -> None:
    report = run()
    assert report.failed == 0
    assert report.checks > 40


def test_the_tail_reports_the_promise_count() -> None:
    tail = run().render().splitlines()[-1]
    assert tail.startswith("selftest: ")
    assert tail.endswith("failed")


def test_the_promises_answer_twice_the_same() -> None:
    first, second = run(), run()
    assert (first.checks, first.failed) == (second.checks, second.failed)


def test_the_marker_lives_in_the_walker() -> None:
    marker = " ".join((walk_module.__doc__ or "").split()).lower()
    assert FIXTURE.lower() in marker


def test_a_broken_claim_is_counted() -> None:
    report = Report()
    report.ok("a promise holds", True)
    report.ok("a promise fails", False)
    report.equal("a pair differs", 1, 2)
    assert (report.checks, report.failed) == (3, 2)
    assert "selftest: 1 checks passed, 2 failed" in report.render()


def test_a_refusal_is_a_check() -> None:
    report = Report()
    report.refuses("noise is refused", lambda: int("a"), ValueError)
    report.refuses("quiet is refused", lambda: len(""), ValueError)
    assert (report.checks, report.failed) == (2, 1)
