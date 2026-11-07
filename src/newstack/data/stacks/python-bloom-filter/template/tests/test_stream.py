"""Seeded streams: same seed, same answers; the fixture replays them."""

from __future__ import annotations

import pytest

from {{ package_name }}.stream import (
    FIXTURE,
    LENGTH,
    Plan,
    StreamError,
    load_fixture,
    stream,
    write_fixture,
)
from {{ package_name }}.universe import UNIVERSE


def test_the_stream_replays() -> None:
    assert stream(7) == stream(7)
    assert stream(2026, 8) == stream(2026, 8)


def test_the_stream_is_the_shipped_length_by_default() -> None:
    assert LENGTH == 32
    drawn = stream(13)
    assert len(drawn) == LENGTH
    assert len(set(drawn)) == LENGTH


@pytest.mark.parametrize("seed", [0, 7, 42, 2026])
def test_every_key_stays_in_the_universe(seed: int) -> None:
    for key in stream(seed, 64):
        assert 0 <= key < UNIVERSE


@pytest.mark.parametrize("length", [0, -1, 257, 2.0])
def test_strange_counts_leave_the_stream(length: object) -> None:
    with pytest.raises(StreamError):
        stream(7, length)  # type: ignore[arg-type]


def test_a_plan_carries_its_seed_and_keys() -> None:
    plan = Plan.draw(9)
    assert plan.seed == 9
    assert plan.keys == stream(9)
    assert plan.length == LENGTH


def test_the_fixture_replays_the_arithmetic() -> None:
    plans = load_fixture(FIXTURE)
    assert len(plans) == 5
    for plan in plans:
        assert plan.keys == stream(plan.seed)
        assert plan.length == LENGTH


def test_a_written_fixture_reads_back_plan_for_plan(tmp_path_factory: object) -> None:
    import tempfile

    plans = load_fixture(FIXTURE)
    with tempfile.TemporaryDirectory() as room:
        path = f"{room}/streams.txt"
        write_fixture(path, plans)
        assert load_fixture(path) == plans


@pytest.mark.parametrize(
    "body",
    [
        "# only noise\n",
        "7 2 165\n",  # promised 2, holds 1
        "x 32 " + " ".join(["1"] * 32) + "\n",
        "7 32 " + " ".join(["1"] * 31) + "\n",
    ],
)
def test_a_broken_fixture_is_named_not_guessed(body: str) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as room:
        path = f"{room}/streams.txt"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(body)
        with pytest.raises(StreamError):
            load_fixture(path)


def test_a_missing_fixture_is_named() -> None:
    with pytest.raises(StreamError):
        load_fixture(f"{FIXTURE}.missing")
