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
    assert synthetic(12, seed=3) == synthetic(12, seed=3)
    assert synthetic(12, seed=3) != synthetic(12, seed=4)
    assert synthetic(12) == synthetic(12, seed=DEFAULT_SEED)


def test_zero_keys_are_refused() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)


def test_a_list_round_trips(tmp_path) -> None:
    corpus = synthetic(8, seed=11)
    path = tmp_path / "keys.txt"
    write_keys(corpus, str(path))
    assert load_keys(str(path)) == corpus


def test_noise_and_nothing_are_refused(tmp_path) -> None:
    noise = tmp_path / "noise.txt"
    noise.write_text("# comment\n\n7.5\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_keys(str(noise))
    empty = tmp_path / "empty.txt"
    empty.write_text("# nothing\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_keys(str(empty))
    with pytest.raises(CorpusError):
        load_keys(str(tmp_path / "missing.txt"))


def test_a_snapshot_replays_itself() -> None:
    corpus = synthetic(6, seed=2)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert list(thawed.keys) == corpus
    assert thawed.seed == DEFAULT_SEED
    with pytest.raises(CorpusError):
        Snapshot.loads('{"seed": 1}')
