from __future__ import annotations

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

FIXTURE = "fixtures/keys.txt"


def test_the_generator_is_deterministic() -> None:
    assert synthetic(60, seed=5) == synthetic(60, seed=5)
    assert synthetic(60, seed=5) != synthetic(60, seed=6)


def test_the_generator_hands_out_distinct_keys() -> None:
    pairs = synthetic(60, seed=5)
    assert len({key for key, _ in pairs}) == 60


def test_the_monotone_stream_rises() -> None:
    stream = monotone(32, seed=4)
    assert [key for key, _ in stream] == sorted(key for key, _ in stream)
    assert len({key for key, _ in stream}) == 32


@pytest.mark.parametrize("builder", [synthetic, monotone])
def test_a_corpus_of_zero_is_no_corpus(builder) -> None:
    with pytest.raises(StreamError):
        builder(0)


def test_a_snapshot_replays_itself() -> None:
    pairs = synthetic(10, seed=3)
    frozen = Snapshot(pairs, DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert thawed.pairs == pairs
    assert thawed.seed == DEFAULT_SEED


def test_half_a_snapshot_is_no_snapshot() -> None:
    with pytest.raises(StreamError):
        Snapshot.loads('{"seed": 1}')


def test_a_written_stream_reads_back(tmp_path) -> None:
    pairs = synthetic(12, seed=9)
    path = tmp_path / "keys.txt"
    write_keys(pairs, str(path))
    assert load_keys(str(path)) == pairs


def test_comments_and_blanks_are_skipped(tmp_path) -> None:
    path = tmp_path / "quiet.txt"
    path.write_text("# a comment\n\n7 1\n\n# another\n8 2\n", encoding="utf-8")
    assert load_keys(str(path)) == [(7, 1), (8, 2)]


def test_a_missing_stream_is_named(tmp_path) -> None:
    with pytest.raises(StreamError, match="cannot read"):
        load_keys(str(tmp_path / "nowhere.txt"))


def test_a_stream_of_noise_is_refused(tmp_path) -> None:
    path = tmp_path / "noise.txt"
    path.write_text("1 x\n", encoding="utf-8")
    with pytest.raises(StreamError, match="non-integer"):
        load_keys(str(path))


def test_a_stream_of_nothing_is_refused(tmp_path) -> None:
    path = tmp_path / "empty.txt"
    path.write_text("# only a comment\n", encoding="utf-8")
    with pytest.raises(StreamError, match="no keys"):
        load_keys(str(path))


def test_the_codex_is_a_sorted_stream_of_whole_numbers() -> None:
    pairs = load_keys(FIXTURE)
    keys = [key for key, _ in pairs]
    assert len(keys) >= 20
    assert keys == sorted(keys)
    assert all(key >= 0 for key in keys)
