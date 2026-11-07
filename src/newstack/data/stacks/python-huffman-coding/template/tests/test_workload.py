from __future__ import annotations

from {{ package_name }}.workload import (
    Storm,
    WorkloadError,
    honest_streams,
    run_storm,
)

DEFAULT_STEPS = 140


def test_the_storm_checks_more_than_it_steps() -> None:
    storm = run_storm(steps=40)
    assert isinstance(storm, Storm)
    assert storm.checks > storm.steps
    assert storm.breaks == ()
    assert storm.seated


def test_the_storm_is_seeded_and_deterministic() -> None:
    assert run_storm(seed=9, steps=20) == run_storm(seed=9, steps=20)


def test_the_default_storm_is_the_documented_size() -> None:
    assert run_storm().steps == DEFAULT_STEPS


def test_a_storm_refuses_nonsense() -> None:
    for bad in (0, -3):
        try:
            run_storm(steps=bad)
        except WorkloadError:
            continue
        raise AssertionError(f"{bad} steps is no storm")


def test_honest_streams_silences_a_seeded_corpus() -> None:
    assert honest_streams(24)
    assert honest_streams(8, seed=13)
