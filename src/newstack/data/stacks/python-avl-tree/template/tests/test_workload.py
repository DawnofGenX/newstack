from __future__ import annotations

import pytest

from {{ package_name }}.workload import (
    WorkloadError,
    rebuild_matches,
    run_storm,
)


def test_the_storm_breaks_nothing() -> None:
    for seed in (5, 55, 555):
        storm = run_storm(seed=seed)
        assert storm.breaks == 0
        assert storm.seated
        assert storm.checks > storm.steps


def test_the_storm_needs_steps() -> None:
    with pytest.raises(WorkloadError):
        run_storm(steps=0)
    with pytest.raises(WorkloadError):
        run_storm(pool=0)


def test_rebuilt_trees_answer_alike() -> None:
    assert rebuild_matches([8, 32])
