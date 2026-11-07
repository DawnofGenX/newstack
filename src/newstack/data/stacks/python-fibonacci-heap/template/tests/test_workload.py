from __future__ import annotations

import pytest

from {{ package_name }}.workload import (
    WorkloadError,
    decrease_holds,
    replay_matches,
    run_storm,
)


@pytest.mark.parametrize("seed", [13, 77, 101])
def test_a_storm_never_disagrees_with_the_sort(seed: int) -> None:
    storm = run_storm(seed=seed)
    assert storm.breaks == 0
    assert storm.seated
    assert storm.exact
    assert storm.decreases > 0
    assert storm.checks > storm.steps
    assert storm.max_degree <= storm.bound


def test_a_quiet_heap_replays_the_sort() -> None:
    assert replay_matches([9, 40, -3, 0, 40])


def test_a_decreased_forest_stays_ordered() -> None:
    assert decrease_holds([8, 4, 6], 1, -2)
    assert not decrease_holds([8, 4, 6], 0, 99)


def test_a_storm_without_bounds_is_refused() -> None:
    with pytest.raises(WorkloadError, match="whole-number"):
        run_storm(steps=0)
    with pytest.raises(WorkloadError, match="whole-number"):
        run_storm(seed=1.5)
