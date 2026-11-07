from __future__ import annotations

import pytest

from {{ package_name }}.streams import (
    DEFAULT_SEED,
    Snapshot,
    StreamError,
    load_values,
    rising,
    synthetic,
    write_values,
)


def test_the_generator_is_deterministic() -> None:
    assert synthetic(60, seed=5) == synthetic(60, seed=5)
    assert len(synthetic(60, seed=5)) == 60


def test_the_rising_stream_rises() -> None:
    climb = rising(32, seed=4)
    assert climb == sorted(climb)
    assert len(climb) == 32


def test_a_corpus_of_zero_is_no_corpus() -> None:
    with pytest.raises(StreamError):
        synthetic(0)
    with pytest.raises(StreamError):
        rising(0)
    with pytest.raises(StreamError):
        synthetic(4, seed="five")  # type: ignore[arg-type]


def test_a_snapshot_replays_its_values_and_seed() -> None:
    values = synthetic(24, seed=9)
    frozen = Snapshot(values, DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert thawed.values == values
    assert thawed.seed == DEFAULT_SEED


def test_half_a_snapshot_is_no_snapshot() -> None:
    with pytest.raises(StreamError):
        Snapshot.loads('{"seed": 1}')
    with pytest.raises(StreamError):
        Snapshot.loads('{"values": ["one"], "seed": 1}')


def test_a_written_list_reads_back(tmp_path) -> None:
    values = synthetic(12, seed=3)
    path = tmp_path / "values.txt"
    write_values(values, str(path))
    assert load_values(str(path)) == values


def test_blanks_and_comments_are_skipped(tmp_path) -> None:
    path = tmp_path / "quiet.txt"
    path.write_text("# a comment\n\n-5\n\n7\n", encoding="utf-8")
    assert load_values(str(path)) == [-5, 7]


def test_a_missing_or_noisy_list_is_named(tmp_path) -> None:
    with pytest.raises(StreamError):
        load_values(str(tmp_path / "missing.txt"))
    noise = tmp_path / "noise.txt"
    noise.write_text("# a comment\n\nseven\n", encoding="utf-8")
    with pytest.raises(StreamError):
        load_values(str(noise))
    empty = tmp_path / "empty.txt"
    empty.write_text("# nothing but comments\n", encoding="utf-8")
    with pytest.raises(StreamError):
        load_values(str(empty))
