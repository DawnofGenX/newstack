from __future__ import annotations

import pytest

from {{ package_name }}.suffix import SuffixArray
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
        assert storm.seated
        assert storm.clean
        assert storm.checks > storm.steps
        assert storm.builds > 0


def test_the_storm_holds_a_real_census() -> None:
    for seed in SEEDS:
        storm = run_storm(steps=220, seed=seed, pool=20)
        assert storm.breaks == 0
        assert storm.builds >= 1


def test_a_storm_without_steps_is_refused() -> None:
    with pytest.raises(WorkloadError):
        run_storm(steps=0)
    with pytest.raises(WorkloadError):
        run_storm(pool=0)


def test_rebuilt_tables_answer_alike() -> None:
    texts = ["banana", "mississippi", "aaaa", "abcabcabc"]
    assert rebuild_matches(texts)
    assert rebuild_matches(["a", "bb", "ccc"])
    first = SuffixArray("banana")
    second = SuffixArray("banana")
    assert first.array == second.array
    assert first.lcp_array() == second.lcp_array()
