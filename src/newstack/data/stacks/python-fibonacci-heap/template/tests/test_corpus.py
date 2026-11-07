from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_items,
    synthetic,
    write_items,
)


def test_the_generator_is_deterministic() -> None:
    assert synthetic(12, seed=3) == synthetic(12, seed=3)
    assert synthetic(12, seed=3) != synthetic(12, seed=4)
    assert synthetic(5) == synthetic(5, seed=DEFAULT_SEED)


def test_zero_items_is_refused() -> None:
    with pytest.raises(CorpusError, match="no items"):
        synthetic(0)


def test_a_written_list_reads_back(tmp_path) -> None:
    keys = synthetic(9, seed=8)
    path = str(tmp_path / "items.txt")
    write_items(keys, path)
    assert load_items(path) == keys


def test_comments_and_blanks_are_skipped(tmp_path) -> None:
    path = str(tmp_path / "odd.txt")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("# a comment\n\n7\n\n-3\n")
    assert load_items(path) == [7, -3]


def test_noise_and_absence_are_named(tmp_path) -> None:
    with pytest.raises(CorpusError, match="no such item list"):
        load_items(str(tmp_path / "missing.txt"))
    noise = str(tmp_path / "noise.txt")
    with open(noise, "w", encoding="utf-8") as handle:
        handle.write("7.5\n")
    with pytest.raises(CorpusError, match="not an integer"):
        load_items(noise)


def test_a_snapshot_replays_its_items() -> None:
    frozen = Snapshot((1, 2, 3), 9)
    thawed = Snapshot.loads(frozen.dumps())
    assert thawed.keys == (1, 2, 3)
    assert thawed.seed == 9
    with pytest.raises(CorpusError, match="half a snapshot"):
        Snapshot.loads('{"seed": 1}')
