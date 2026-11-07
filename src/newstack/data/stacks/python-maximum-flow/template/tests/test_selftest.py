from __future__ import annotations

from {{ package_name }}.selftest import (
    FIXTURE,
    Report,
    run,
)


def test_the_promises_answer_quiet() -> None:
    report = run()
    assert report.failed == 0
    assert report.checks > 30


def test_the_tail_names_the_tally() -> None:
    tail = run().render().splitlines()[-1]
    assert tail.startswith("selftest: ")
    assert tail.endswith("0 failed")


def test_a_report_counts_what_it_is_told() -> None:
    report = Report()
    report.equal("a promise", 1, 1)
    report.equal("a broken promise", 1, 2)
    assert (report.checks, report.failed) == (2, 1)


def test_the_marker_lives_where_the_detector_reaches() -> None:
    from {{ package_name }} import solve as solve_module

    assert FIXTURE in " ".join((solve_module.__doc__ or "").split()).lower()
