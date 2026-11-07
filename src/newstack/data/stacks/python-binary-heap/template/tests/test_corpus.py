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


def test_the_generator_is_deterministic_and_distinct() -> None:
    keys = synthetic(20, seed=5)
    assert keys == synthetic(20, seed=5)
    assert len(set(keys)) == 20
    assert keys == sorted(keys)


def test_no_keys_from_zero() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)


def test_a_written_list_reads_back(tmp_path) -> None:
    keys = synthetic(12, seed=3)
    path = tmp_path / "keys.txt"
    write_keys(keys, str(path))
    assert load_keys(str(path)) == keys


def test_noise_and_missing_lists_are_named(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_keys(str(tmp_path / "missing.txt"))
    noise = tmp_path / "noise.txt"
    noise.write_text("# a comment\n\n7.5\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_keys(str(noise))
    empty = tmp_path / "empty.txt"
    empty.write_text("# nothing\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_keys(str(empty))


def test_a_snapshot_replays_its_keys() -> None:
    keys = synthetic(8, seed=9)
    frozen = Snapshot(tuple(keys), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert list(thawed.keys) == keys
    assert thawed.seed == DEFAULT_SEED
    with pytest.raises(CorpusError):
        Snapshot.loads('{"seed": 1}')
