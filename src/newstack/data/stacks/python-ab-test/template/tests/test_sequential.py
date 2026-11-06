"""Peeking is a choice about error, and the boundary is what buys it back."""

from __future__ import annotations

import pytest

from {{ package_name }} import sequential as subject


def test_the_boundary_is_strict_early_and_plain_at_the_end() -> None:
    boundary = subject.obrien_fleming(0.05, 10)
    assert boundary.at(1) == pytest.approx(6.198, abs=1e-3)
    assert boundary.at(10) == pytest.approx(1.96, abs=1e-2)
    assert boundary.at(1) > boundary.at(5) > boundary.at(10)


def test_the_spending_table_adds_up_to_more_than_alpha() -> None:
    boundary = subject.obrien_fleming(0.05, 5)
    assert sum(boundary.spent) > 0.05
    assert boundary.spent[-1] == pytest.approx(0.05, abs=1e-6)


def test_an_impossible_boundary_is_refused() -> None:
    with pytest.raises(subject.StatsError, match="a boundary needs at least one look"):
        subject.obrien_fleming(0.05, 0)
    with pytest.raises(subject.StatsError, match="alpha needs to be a probability"):
        subject.obrien_fleming(1.5, 5)
    with pytest.raises(subject.StatsError, match="outside 1"):
        subject.obrien_fleming(0.05, 5).at(6)


def test_the_boundary_table_is_printable() -> None:
    rows = subject.obrien_fleming(0.05, 3).lines()
    assert rows[0].startswith("look")
    assert len(rows) == 4


def test_peeking_never_crosses_more_often_than_the_flat_line() -> None:
    world = subject.simulate(trials=200, visitors=400, looks=5, seed=3)
    assert 0 <= world.guarded_crossings <= world.peeking_crossings <= world.trials
    assert 0 <= world.fixed_crossings <= world.trials
    assert world.rate(world.peeking_crossings) == world.peeking_crossings / 200


def test_the_same_seed_reproduces_the_same_worlds() -> None:
    first = subject.simulate(trials=100, visitors=400, looks=5, seed=11)
    second = subject.simulate(trials=100, visitors=400, looks=5, seed=11)
    assert first == second


def test_the_flat_line_spends_more_than_one_look() -> None:
    world = subject.simulate(trials=400, visitors=2000, looks=10, seed=7)
    assert world.peeking_crossings > world.fixed_crossings


def test_a_simulation_needs_sensible_inputs() -> None:
    with pytest.raises(subject.StatsError, match="baseline rate is a probability"):
        subject.simulate(baseline=2.0)
    with pytest.raises(subject.StatsError, match="cannot fill"):
        subject.simulate(visitors=3, looks=10)
    with pytest.raises(subject.StatsError, match="at least one trial"):
        subject.simulate(trials=0)


def test_the_report_names_three_policies() -> None:
    text = "\n".join(subject.simulate(trials=20, visitors=200, looks=4).lines())
    assert "one look" in text
    assert "every look" in text
    assert "boundary" in text
