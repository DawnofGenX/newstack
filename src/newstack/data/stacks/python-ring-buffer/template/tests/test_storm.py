from __future__ import annotations

import pytest

from {{ package_name }}.storm import (
    StormError,
    drain_matches,
    run_storm,
    storm_matches,
)


def test_the_storm_breaks_nothing() -> None:
    for seed in (5, 55, 555):
        storm = run_storm(seed=seed)
        assert storm.breaks == 0
        assert storm.seated
        assert storm.checks > storm.steps
        assert storm.clean


def test_the_storm_needs_steps_and_slots() -> None:
    with pytest.raises(StormError):
        run_storm(steps=0)
    with pytest.raises(StormError):
        run_storm(capacity=0)


@pytest.mark.parametrize("capacity", (1, 5, 16))
def test_buffers_answer_like_the_deque(capacity: int) -> None:
    assert storm_matches(capacity, 4242)
    assert drain_matches(capacity, list(range(capacity * 3)))
