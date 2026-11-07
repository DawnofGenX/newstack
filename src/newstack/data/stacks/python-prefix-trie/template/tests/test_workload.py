from __future__ import annotations

import pytest

from {{ package_name }}.trie import PrefixTrie
from {{ package_name }}.workload import (
    DEFAULT_STEPS,
    WorkloadError,
    rebuild_matches,
    run_storm,
)

SEEDS = (13, 31, 77, 4099)


def test_the_storm_breaks_nothing_and_stays_seated() -> None:
    for seed in SEEDS:
        storm = run_storm(seed=seed)
        assert storm.steps == DEFAULT_STEPS
        assert storm.breaks == 0
        assert storm.ordered
        assert storm.clean
        assert storm.checks > storm.steps


def test_the_storm_holds_a_real_census() -> None:
    for seed in SEEDS:
        storm = run_storm(steps=240, seed=seed, pool=40)
        assert 0 <= storm.words <= 40
        assert storm.breaks == 0


def test_a_storm_without_steps_is_refused() -> None:
    with pytest.raises(WorkloadError):
        run_storm(steps=0)
    with pytest.raises(WorkloadError):
        run_storm(pool=0)


def test_two_tries_one_corpus_answer_alike() -> None:
    corpus = ["car", "cart", "cartwheel", "dog", "dogma"]
    assert rebuild_matches(corpus)
    assert rebuild_matches(["a", "bb", "ccc"])
    first = PrefixTrie(corpus)
    second = PrefixTrie(reversed(corpus))
    assert first.walk() == second.walk() == sorted(corpus)
