from __future__ import annotations

import pytest

from {{ package_name }}.workload import (
    STEPS,
    Replay,
    WorkloadError,
    run_monotone,
    run_workload,
)


def test_the_mixed_storm_answers_sorted() -> None:
    storm = run_workload(seed=13)
    assert storm.steps == STEPS
    assert storm.breaks == 0
    assert storm.sorted_held
    assert storm.checks > storm.steps


def test_the_mixed_storm_is_a_replay() -> None:
    left = run_workload(seed=13)
    right = run_workload(seed=13)
    assert (left.steps, left.checks, left.rebuilds) == (
        right.steps,
        right.checks,
        right.rebuilds,
    )


def test_a_monotone_stream_spends_no_rebuild() -> None:
    forward = run_monotone(seed=11, size=64)
    assert forward.rebuilds == 0
    assert forward.breaks == 0
    assert forward.sorted_held


def test_a_monotone_stream_of_one_is_a_stream() -> None:
    forward = run_monotone(seed=2, size=1)
    assert forward.rebuilds == 0
    assert forward.sorted_held


def test_a_storm_outside_its_bounds_is_refused() -> None:
    with pytest.raises(WorkloadError):
        run_workload(steps=0)
    with pytest.raises(WorkloadError):
        run_monotone(size=0)


def test_the_replay_records_what_a_storm_spent() -> None:
    storm = run_workload(seed=5, steps=12)
    assert isinstance(storm, Replay)
    assert storm.steps == 12
