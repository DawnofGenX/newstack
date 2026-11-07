from __future__ import annotations

import random

import pytest

from {{ package_name }}.corpus import synthetic
from {{ package_name }}.workload import (
    DEFAULT_STEPS,
    Replay,
    WorkloadError,
    rebuild_matches,
    run_storm,
)

SEEDS = (13, 77, 2026)


def test_a_storm_runs_its_steps_and_breaks_nothing() -> None:
    for seed in SEEDS:
        storm = run_storm(seed=seed)
        assert storm.steps == DEFAULT_STEPS
        assert storm.breaks == 0
        assert storm.seated
        assert storm.checks > storm.steps
        assert storm.points > 0


def test_a_storm_is_deterministic_per_seed() -> None:
    first = run_storm(steps=60, seed=31)
    second = run_storm(steps=60, seed=31)
    assert (first.points, first.checks, first.breaks) == \
        (second.points, second.checks, second.breaks)


def test_the_gate_of_a_storm() -> None:
    for bad in ((0, 5), (10, 0), (-3, 5)):
        with pytest.raises(WorkloadError):
            run_storm(steps=bad[0], pool=bad[1])


def test_rebuilt_trees_answer_identically() -> None:
    for seed in (7, 91):
        assert rebuild_matches(synthetic(60, seed=seed), seed=seed)


def test_a_shuffled_corpus_rebuilds_identically() -> None:
    corpus = synthetic(50, seed=19)
    shuffled = random.Random(19).sample(corpus, len(corpus))
    assert rebuild_matches(shuffled, seed=19)


def test_the_replay_shape() -> None:
    storm = run_storm(steps=20, seed=3)
    assert isinstance(storm, Replay)
    assert storm.steps == 20
