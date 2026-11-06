from __future__ import annotations

import pytest

from {{ package_name }}.coins import (
    CoinToss,
    CoinTossError,
    LevelPlan,
    expected_level,
    level_budget,
)


def test_one_seed_replays_one_ladder() -> None:
    assert CoinToss(seed=7).plan(50).levels == CoinToss(seed=7).plan(50).levels


def test_a_different_seed_shuffles_the_ladder() -> None:
    assert CoinToss(seed=7).plan(50).levels != CoinToss(seed=8).plan(50).levels


def test_a_level_never_outruns_its_cap() -> None:
    assert all(level < 4 for level in CoinToss(7, cap=4).plan(200).levels)


def test_expected_level_tracks_log2() -> None:
    assert expected_level(1) == 1
    assert expected_level(1024) == 11
    assert level_budget(1024) <= 16


def test_the_plan_counts_what_the_flips_cost() -> None:
    plan = CoinToss(seed=1).plan(30)
    assert isinstance(plan, LevelPlan)
    assert plan.flips >= 30
    assert plan.tallest == max(plan.levels)
    assert plan.mean_level > 0


def test_a_fork_still_answers_from_the_same_seed() -> None:
    assert CoinToss(seed=5).fork(2).seed == 7


def test_a_seed_must_be_a_number() -> None:
    with pytest.raises(CoinTossError):
        CoinToss(seed="seven")  # type: ignore[arg-type]


def test_a_cap_of_zero_holds_no_tower() -> None:
    with pytest.raises(CoinTossError):
        CoinToss(cap=0)
