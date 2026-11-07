from __future__ import annotations

from {{ package_name }}.workload import (
    WorkloadError,
    rebuild_matches,
    run_storm,
)

WORDS = ["ana", "abra", "anana", "aa", ""]


def test_the_storm_runs_and_breaks_nothing() -> None:
    for seed in (11, 91):
        storm = run_storm(seed=seed)
        assert storm.steps == 140
        assert storm.breaks == ()
        assert storm.seated
        assert storm.checks >= storm.steps


def test_the_storm_is_deterministic() -> None:
    assert run_storm(seed=3).breaks == run_storm(seed=3).breaks


def test_the_storm_refuses_no_steps() -> None:
    try:
        run_storm(steps=0)
    except WorkloadError:
        return
    raise AssertionError("a storm without steps slipped through")


def test_recut_arrays_answer_alike() -> None:
    assert rebuild_matches(WORDS)
    assert rebuild_matches([])
