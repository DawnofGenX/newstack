"""The selftest's own ledger: the Report counts what it promises."""

from __future__ import annotations

from {{ package_name }}.selftest import (
    KEYS,
    Report,
    run,
)

REPORT = run()


def test_the_report_is_a_ledger_of_its_own_promises() -> None:
    assert REPORT.failed == 0
    assert REPORT.checks > 100
    tail = REPORT.render().splitlines()[-1]
    assert tail == f"selftest: {REPORT.checks} checks passed, 0 failed"


def test_the_gate_keys_are_all_of_the_promised_domain() -> None:
    assert len(KEYS) == 8
    assert min(KEYS) == 0
    assert max(KEYS) == 255


def test_a_refusal_is_a_check_not_a_crash() -> None:
    report = Report()
    report.refuses("a refusal", lambda: (_ for _ in ()).throw(ValueError), ValueError)
    report.equal("an agreement", 1, 1)
    assert report.checks == 2
    assert report.failed == 0


def test_a_missed_refusal_fails_the_ledger() -> None:
    report = Report()
    report.refuses("nothing raised", lambda: None, ValueError)
    assert report.checks == 1
    assert report.failed == 1
