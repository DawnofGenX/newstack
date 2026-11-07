from __future__ import annotations

from tempfile import TemporaryDirectory

import pytest

from {{ package_name }}.streams import (
    DEFAULT_SEED,
    Snapshot,
    StreamError,
    load_keys,
    monotone,
    synthetic,
    write_keys,
)


def test_the_generator_is_deterministic() -> None:
    assert synthetic(60, seed=5) == synthetic(60, seed=5)
    assert len(synthetic(60, seed=5)) == 60


def test_a_forest_takes_negative_keys() -> None:
    assert any(key < 0 for key, _ in synthetic(200, seed=5))


def test_the_monotone_stream_rises() -> None:
    stream = monotone(32, seed=4)
    assert [key for key, _ in stream] == sorted(key for key, _ in stream)


def test_a_snapshot_freezes_and_thaws() -> None:
    pairs = synthetic(10, seed=3)
    thawed = Snapshot.loads(Snapshot(pairs, DEFAULT_SEED).dumps())
    assert thawed.pairs == pairs
    assert thawed.seed == DEFAULT_SEED


def test_a_written_stream_reads_back(tmp_path=None) -> None:
    from tempfile import mkdtemp

    room = mkdtemp()
    pairs = synthetic(12, seed=2)
    write_keys(pairs, f"{room}/keys.txt")
    assert load_keys(f"{room}/keys.txt") == pairs


@pytest.mark.parametrize(
    ("call", "error"),
    [
        (lambda: synthetic(0), StreamError),
        (lambda: monotone(0), StreamError),
        (lambda: Snapshot.loads('{"seed": 1}'), StreamError),
    ],
)
def test_half_a_thing_is_no_thing(call: object, error: type[Exception]) -> None:
    with pytest.raises(error):
        call()  # type: ignore[operator]


def test_a_stream_of_noise_is_refused() -> None:
    with TemporaryDirectory() as room:
        noise = f"{room}/noise.txt"
        with open(noise, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\n1 x\n")
        with pytest.raises(StreamError):
            load_keys(noise)
        with pytest.raises(StreamError):
            load_keys(f"{room}/missing.txt")
