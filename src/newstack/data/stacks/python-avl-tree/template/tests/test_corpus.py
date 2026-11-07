from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_keys,
    synthetic,
    write_keys,
)


def test_the_generator_is_deterministic() -> None:
    assert synthetic(15, seed=9) == synthetic(15, seed=9)
    assert len(set(synthetic(15, seed=9))) == 15
    assert synthetic(15, seed=9) == sorted(synthetic(15, seed=9))


def test_zero_is_no_count() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)


def test_a_list_writes_and_reads(tmp_path) -> None:
    path = str(tmp_path / "keys.txt")
    keys = synthetic(12, seed=4)
    write_keys(keys, path)
    assert load_keys(path) == keys


def test_comments_and_blanks_are_skipped(tmp_path) -> None:
    path = tmp_path / "keys.txt"
    path.write_text("# comment\n\n7\n\n-3\n", encoding="utf-8")
    assert load_keys(str(path)) == [7, -3]


def test_noise_and_missing_are_named(tmp_path) -> None:
    noise = tmp_path / "noise.txt"
    noise.write_text("7\n1.5\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_keys(str(noise))
    with pytest.raises(CorpusError):
        load_keys(str(tmp_path / "missing.txt"))
    empty = tmp_path / "empty.txt"
    empty.write_text("# nothing\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_keys(str(empty))


def test_a_snapshot_replays(tmp_path) -> None:
    keys = synthetic(10, seed=2)
    frozen = Snapshot(tuple(keys), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert list(thawed.keys) == keys
    assert thawed.seed == DEFAULT_SEED
    with pytest.raises(CorpusError):
        Snapshot.loads('{"seed": 1}')
