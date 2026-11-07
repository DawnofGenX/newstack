from __future__ import annotations

import pytest

from {{ package_name }}.fenwick import FenwickError
from {{ package_name }}.workload import (
    STEPS,
    Replay,
    WorkloadError,
    ensure_bounds,
    run_storm,
    run_walks,
    run_workload,
)


def test_the_storm_answers_the_list_reference() -> None:
    storm = run_workload(seed=13)
    assert storm.steps == STEPS
    assert storm.breaks == 0
    assert storm.exact
    assert storm.checks > storm.steps
    assert storm.longest <= storm.limit


def test_the_storm_is_a_replay() -> None:
    left = run_workload(seed=13)
    right = run_workload(seed=13)
    assert (left.steps, left.checks, left.breaks) == (
        right.steps,
        right.checks,
        right.breaks,
    )


def test_the_walk_census_keeps_the_bound() -> None:
    census = run_walks(seed=31, size=512)
    assert census.breaks == 0
    assert census.longest <= census.limit
    assert census.limit == 10


def test_a_rebuild_storm_stays_honest() -> None:
    storm = run_storm(seed=23)
    assert storm.breaks == 0
    assert isinstance(storm, Replay)
    assert storm.exact


def test_a_storm_outside_its_bounds_is_refused() -> None:
    with pytest.raises(WorkloadError):
        run_workload(steps=0)
    with pytest.raises(WorkloadError):
        run_walks(size=0)
    with pytest.raises(WorkloadError):
        run_storm(steps=1)


def test_bounds_answer_or_refuse() -> None:
    assert ensure_bounds(0, 10) == 0
    assert ensure_bounds(10, 10) == 10
    with pytest.raises(FenwickError):
        ensure_bounds(11, 10)
