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
    assert all(0 <= key < 256 for key in synthetic(15, seed=9))


def test_the_universe_bounds_the_generator() -> None:
    assert len(synthetic(256, seed=3)) == 256
    with pytest.raises(CorpusError):
        synthetic(257)
    with pytest.raises(CorpusError):
        synthetic(0)


def test_a_list_writes_and_reads(tmp_path) -> None:
    path = str(tmp_path / "keys.txt")
    keys = synthetic(12, seed=4)
    write_keys(keys, path)
    assert load_keys(path) == keys


def test_comments_and_blanks_are_skipped(tmp_path) -> None:
    path = tmp_path / "keys.txt"
    path.write_text("# comment\n\n7\n\n0\n", encoding="utf-8")
    assert load_keys(str(path)) == [7, 0]


def test_noise_and_missing_are_named(tmp_path) -> None:
    noise = tmp_path / "noise.txt"
    noise.write_text("7.5\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_keys(str(noise))
    with pytest.raises(CorpusError):
        load_keys(str(tmp_path / "missing.txt"))


def test_a_snapshot_replays_its_seed() -> None:
    frozen = Snapshot(tuple(synthetic(8, seed=11)), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert thawed.keys == frozen.keys
    assert thawed.seed == DEFAULT_SEED
    with pytest.raises(CorpusError):
        Snapshot.loads('{"seed": 1}')
