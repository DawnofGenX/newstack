from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_values,
    synthetic,
    write_values,
)


def test_the_generator_is_deterministic() -> None:
    assert synthetic(24, seed=7) == synthetic(24, seed=7)
    assert synthetic(24, seed=7) != synthetic(24, seed=8)
    assert len(set(synthetic(32))) == 32


def test_no_values_from_nothing() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)


def test_a_written_list_reads_back(tmp_path) -> None:
    path = str(tmp_path / "values.txt")
    corpus = synthetic(10, seed=3)
    write_values(corpus, path)
    assert load_values(path) == corpus


def test_noise_and_absence_are_named(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_values(str(tmp_path / "missing.txt"))
    noise = tmp_path / "noise.txt"
    noise.write_text("# comment\n\n7.5\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_values(str(noise))
    blank = tmp_path / "blank.txt"
    blank.write_text("\n\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_values(str(blank))


def test_a_snapshot_replays_its_values() -> None:
    corpus = synthetic(6, seed=11)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert list(thawed.values) == corpus
    assert thawed.seed == DEFAULT_SEED
    with pytest.raises(CorpusError):
        Snapshot.loads('{"seed": 1}')
