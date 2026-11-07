from __future__ import annotations

import pytest

from {{ package_name }}.workload import (
    STEPS,
    Replay,
    WorkloadError,
    run_bound,
    run_workload,
)


def test_the_storm_answers_as_the_slices_sum() -> None:
    storm = run_workload(seed=13)
    assert storm.steps == STEPS
    assert storm.breaks == 0
    assert storm.exact
    assert storm.rebuild_equal
    assert storm.max_visits <= storm.bound


def test_the_storm_is_a_replay() -> None:
    left = run_workload(seed=13)
    right = run_workload(seed=13)
    assert (left.steps, left.checks, left.max_visits) == (
        right.steps,
        right.checks,
        right.max_visits,
    )


def test_every_window_of_a_seeded_array_answers_exact() -> None:
    bound = run_bound(size=48, seed=11)
    assert bound.exact
    assert bound.max_visits <= bound.bound
    assert bound.checks == 1225


def test_a_storm_outside_its_bounds_is_refused() -> None:
    with pytest.raises(WorkloadError):
        run_workload(steps=0)
    with pytest.raises(WorkloadError):
        run_bound(size=0)


def test_the_replay_records_what_a_storm_spent() -> None:
    storm = run_workload(seed=5, steps=12)
    assert isinstance(storm, Replay)
    assert storm.steps == 12
