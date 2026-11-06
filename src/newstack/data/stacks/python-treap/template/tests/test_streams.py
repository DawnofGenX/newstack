from __future__ import annotations

import pytest

from {{ package_name }}.streams import (
    Snapshot,
    StreamError,
    load_keys,
    synthetic,
    write_keys,
)


def test_the_generator_is_deterministic() -> None:
    assert synthetic(60, seed=5) == synthetic(60, seed=5)
    assert synthetic(60, seed=5) != synthetic(60, seed=6)


def test_the_generated_keys_are_distinct() -> None:
    pairs = synthetic(120, seed=2)
    assert len({key for key, _ in pairs}) == 120


@pytest.mark.parametrize("count", [0, -1, 2.5, True])
def test_sizes_that_build_no_tree_are_refused(count: object) -> None:
    with pytest.raises(StreamError):
        synthetic(count)  # type: ignore[arg-type]


def test_a_written_stream_reads_back(tmp_path) -> None:
    pairs = synthetic(30, seed=8)
    path = tmp_path / "keys.txt"
    write_keys(pairs, path)
    assert load_keys(path) == pairs


def test_comments_and_blanks_are_skipped(tmp_path) -> None:
    path = tmp_path / "quiet.txt"
    path.write_text("# nothing\n\n1 10\n\n", encoding="utf-8")
    assert load_keys(path) == [(1, 10)]


def test_noise_is_refused(tmp_path) -> None:
    path = tmp_path / "noise.txt"
    path.write_text("one two\n", encoding="utf-8")
    with pytest.raises(StreamError):
        load_keys(path)
    blank = tmp_path / "blank.txt"
    blank.write_text("# only comments\n", encoding="utf-8")
    with pytest.raises(StreamError):
        load_keys(blank)
    with pytest.raises(StreamError):
        load_keys(tmp_path / "missing.txt")


def test_a_snapshot_replays_its_tree(tmp_path) -> None:
    pairs = synthetic(40, seed=6)
    frozen = Snapshot(pairs, 6)
    thawed = Snapshot.loads(frozen.dumps())
    assert thawed.pairs == pairs
    assert thawed.seed == 6
    with pytest.raises(StreamError):
        Snapshot.loads('{"seed": 6}')
    with pytest.raises(StreamError):
        Snapshot.loads("not json")
