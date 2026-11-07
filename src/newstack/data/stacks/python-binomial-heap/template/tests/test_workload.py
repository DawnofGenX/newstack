from __future__ import annotations

import pytest

from {{ package_name }}.workload import (
    WorkloadError,
    run_meld,
    run_monotone,
    run_workload,
)


def test_the_mixed_storm_holds_shape_and_answers_the_pool() -> None:
    storm = run_workload(seed=13)
    assert storm.steps == 160
    assert storm.breaks == 0
    assert storm.sorted_held
    assert storm.melds > 0
    assert storm.checks > storm.steps


def test_a_meld_drains_as_the_sorted_concat() -> None:
    pair = run_meld(seed=11, left=50, right=37)
    assert pair.steps == 87
    assert pair.sorted_held
    assert pair.shapes_held
    assert pair.breaks == 0
    assert pair.links > 0


def test_a_rising_stream_answers_sorted() -> None:
    forward = run_monotone(seed=11, size=64)
    assert forward.breaks == 0
    assert forward.sorted_held


def test_storms_outside_their_bounds_are_refused() -> None:
    with pytest.raises(WorkloadError):
        run_workload(steps=0)
    with pytest.raises(WorkloadError):
        run_meld(left=0)
    with pytest.raises(WorkloadError):
        run_monotone(size=0)
