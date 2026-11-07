"""The shipped audit: 7920 re-asks, zero breaks, the edge counted."""

from __future__ import annotations

import pytest

from {{ package_name }}.audit import (
    COLLISIONS_AT_DEFAULTS,
    CONFIGS,
    RECHECKS,
    STREAM_SEEDS,
    AuditError,
    Ledger,
    Verdict,
    audit_fixture,
    collision_table,
    estimate_items,
    run_stream,
    shipped_audit,
)
from {{ package_name }}.bloom import ROWS, SEED, WIDTH, Bloom
from {{ package_name }}.stream import FIXTURE, Plan, stream
from {{ package_name }}.universe import UNIVERSE

LEDGER = shipped_audit()


def test_the_re_asks_are_all_booked_and_all_ran() -> None:
    assert len(CONFIGS) * len(STREAM_SEEDS) * sum(range(1, 33)) == RECHECKS
    assert LEDGER.checks == RECHECKS == 7920


def test_no_added_key_was_answered_absent() -> None:
    for verdict in LEDGER.verdicts:
        assert verdict.false_negatives == ()


def test_no_absent_key_answered_present_at_the_shipped_widths() -> None:
    for verdict in LEDGER.verdicts:
        assert verdict.false_positives == ()
    assert LEDGER.breaks == []


def test_every_config_and_stream_handed_down_a_verdict() -> None:
    assert len(LEDGER.verdicts) == len(CONFIGS) * len(STREAM_SEEDS)
    assert all(verdict.clean for verdict in LEDGER.verdicts)


def test_the_audit_refuses_a_plan_that_audits_nothing() -> None:
    with pytest.raises(AuditError):
        run_stream("quiet", 8, 1, 1, Plan(seed=1, keys=(1,)))


def test_a_two_key_plan_re_asks_three_times() -> None:
    verdict = run_stream("quiet", WIDTH, ROWS, SEED, Plan(seed=5, keys=(1, 2)))
    assert verdict.rechecks == 3
    assert isinstance(verdict, Verdict)


def test_the_frozen_streams_pass_through_the_default_shape() -> None:
    ledger = audit_fixture(FIXTURE)
    assert ledger.checks == 5 * sum(range(1, 33))
    assert ledger.breaks == []


def test_a_broken_fixture_path_is_named() -> None:
    with pytest.raises(AuditError):
        audit_fixture(f"{FIXTURE}.missing")


def test_the_collision_edge_is_counted_not_prayed_over() -> None:
    assert COLLISIONS_AT_DEFAULTS == collision_table() == 369
    bloom = Bloom()
    witnesses = [
        (first, second)
        for first in range(UNIVERSE)
        for second in range(first + 1, UNIVERSE)
        if set(bloom.seats_of(first)) & set(bloom.seats_of(second))
    ]
    assert len(witnesses) == COLLISIONS_AT_DEFAULTS
    assert (0, 198) in witnesses


def test_the_estimator_inverts_the_fill() -> None:
    crowded = Bloom(WIDTH, ROWS, SEED)
    for key in stream(7):
        crowded.add(key)
    assert crowded.bits_set == 123
    assert abs(estimate_items(crowded) - 32) < 2.0
    empty = Bloom()
    assert estimate_items(empty) == 0.0
    full = Bloom(8, 1, 0, bits=255)
    assert estimate_items(full) == 256.0


def test_a_ledger_names_its_breaks() -> None:
    ledger = Ledger()
    ledger.verdicts.append(
        Verdict("test", 7, 2, 3, (5,), (9,))
    )
    assert len(ledger.breaks) == 2
    assert ledger.checks == 3
