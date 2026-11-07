from __future__ import annotations

import pytest

from {{ package_name }}.workload import (
    WorkloadError,
    rebuild_matches,
    run_storm,
)


def test_a_storm_breaks_nothing_after_any_op() -> None:
    storm = run_storm(steps=120, seed=13)
    assert storm.breaks == 0
    assert storm.seated
    assert storm.checks > 3 * 120
    assert storm.keys >= 0


def test_a_storm_needs_positive_numbers() -> None:
    with pytest.raises(WorkloadError):
        run_storm(steps=0)
    with pytest.raises(WorkloadError):
        run_storm(pool=0)


def test_rebuild_forgets_the_order() -> None:
    assert rebuild_matches([5, 1, 9, 3])
    assert rebuild_matches([0])
    assert rebuild_matches([-40, 40, -40, 40, 7])
