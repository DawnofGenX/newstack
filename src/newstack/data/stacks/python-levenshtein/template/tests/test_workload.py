from __future__ import annotations

import pytest

from {{ package_name }}.corpus import synthetic
from {{ package_name }}.distance import distance
from {{ package_name }}.workload import (
    DEFAULT_STEPS,
    WorkloadError,
    live_distances,
    run_storm,
    shuffle_matches,
)

SEEDS = (13, 31, 77, 4099)


def test_the_storm_breaks_nothing_across_seeds() -> None:
    for seed in SEEDS:
        storm = run_storm(seed=seed)
        assert storm.steps == DEFAULT_STEPS
        assert storm.breaks == 0
        assert storm.clean
        assert storm.checks > storm.steps
        assert storm.words == 80


def test_a_storm_without_steps_is_refused() -> None:
    with pytest.raises(WorkloadError):
        run_storm(steps=0)
    with pytest.raises(WorkloadError):
        run_storm(pool=0)


def test_corpus_order_is_not_an_answer() -> None:
    assert shuffle_matches(synthetic(80, seed=55))
    assert shuffle_matches(["cart", "cat", "car", "dog"], seed=3)


def test_live_distances_counts_changes() -> None:
    assert live_distances([("cat", "cat"), ("cart", "cat"), ("knight", "light")]) == [
        0,
        1,
        distance("knight", "light"),
    ]
