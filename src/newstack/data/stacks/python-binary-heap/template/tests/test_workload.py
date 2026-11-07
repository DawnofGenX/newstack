from __future__ import annotations

import pytest

from {{ package_name }}.workload import (
    WorkloadError,
    rebuild_matches,
    run_storm,
)

SEEDS = (13, 77, 404)


def test_the_storm_breaks_nothing() -> None:
    for seed in SEEDS:
        storm = run_storm(seed=seed)
        assert storm.steps == 140
        assert storm.breaks == 0
        assert storm.clean
        assert storm.pushes > 0
        assert storm.pops > 0
        assert storm.checks > storm.steps


def test_the_storm_scales_its_steps() -> None:
    storm = run_storm(steps=40, seed=11)
    assert storm.steps == 40
    assert storm.breaks == 0


def test_a_storm_without_steps_is_refused() -> None:
    with pytest.raises(WorkloadError):
        run_storm(steps=0)
    with pytest.raises(WorkloadError):
        run_storm(pool=0)


def test_rebuilt_heaps_answer_alike() -> None:
    assert rebuild_matches([9, 40, -3, 40])
    assert rebuild_matches([])
