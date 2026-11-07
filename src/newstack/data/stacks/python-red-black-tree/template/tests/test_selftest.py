from __future__ import annotations

from {{ package_name }}.selftest import (
    FIXTURE,
    Report,
    run,
)


def test_the_selftest_passes_on_the_shipped_modules() -> None:
    report = run()
    assert report.failed == 0
    assert report.checks > 30
    assert report.render().endswith(
        f"{report.checks} checks passed, 0 failed"
    )


def test_the_report_counts_every_verdict() -> None:
    report = Report()
    report.ok("a held claim", True)
    report.equal("an equal pair", 1, 1)
    report.refuses("a refused junk", lambda: (_ for _ in ()).throw(
        ValueError), ValueError)
    assert report.checks == 3
    assert report.failed == 0
    report.ok("a broken claim", False)
    assert report.failed == 1
    assert "FAIL a broken claim" in "\n".join(report.lines)


def test_refuses_names_the_wrong_exception() -> None:
    report = Report()
    report.refuses("the wrong name", lambda: (_ for _ in ()).throw(
        TypeError), ValueError)
    assert report.failed == 1


def test_the_fixture_phrase_ships_with_the_checker() -> None:
    from {{ package_name }} import check

    assert FIXTURE in " ".join((check.__doc__ or "").split())
