from __future__ import annotations

from {{ package_name }}.workload import (
    WorkloadError,
    honest_streams,
    run_storm,
    stem_repeats,
)


def test_the_storm_closes_every_loop() -> None:
    for seed in (13, 77):
        storm = run_storm(seed=seed)
        assert storm.steps == 140
        assert storm.breaks == ()
        assert storm.seated
        assert storm.checks >= storm.steps


def test_a_storm_without_steps_is_refused() -> None:
    try:
        run_storm(steps=0)
    except WorkloadError:
        return
    raise AssertionError("a storm without steps ran")


def test_seeded_streams_audit_silent() -> None:
    assert honest_streams(24, seed=3)


def test_the_stem_counter_counts_repeats() -> None:
    assert stem_repeats("ababab") == 3
    assert stem_repeats("abra") == 1
    assert stem_repeats("") == 0
