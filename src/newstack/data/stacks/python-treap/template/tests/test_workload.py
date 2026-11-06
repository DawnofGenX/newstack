from __future__ import annotations

import pytest

from {{ package_name }}.workload import Replay, WorkloadError, run_workload


def test_a_storm_leaves_neither_order_broken() -> None:
    replay = run_workload(seed=13)
    assert replay.breaks == 0
    assert replay.steps == 160
    assert replay.checks > replay.steps


def test_the_replay_is_a_replay() -> None:
    assert run_workload(seed=13) == run_workload(seed=13)


def test_the_line_reports_the_storm() -> None:
    replay = run_workload(seed=5, size=8, steps=10)
    assert isinstance(replay, Replay)
    assert "breaks 0" in replay.line()


@pytest.mark.parametrize(
    ("size", "steps"),
    [(0, 10), (-3, 10), (10, 0), (10, -1), (10, 60_000), (6_000, 10)],
)
def test_a_storm_outside_its_bounds_is_refused(size: int, steps: int) -> None:
    with pytest.raises(WorkloadError):
        run_workload(size=size, steps=steps)


def test_the_seed_of_a_storm_must_be_a_number() -> None:
    with pytest.raises(WorkloadError):
        run_workload(seed="thirteen")  # type: ignore[arg-type]
