from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    CorpusError,
    Snapshot,
    load_keys,
    parse_key,
    synthetic,
    write_keys,
)
from {{ package_name }}.keys import MAX_KEY


def test_parse_key_passes_the_gate() -> None:
    assert parse_key(" 7 ") == 7
    assert parse_key("-13") == -13
    with pytest.raises(CorpusError):
        parse_key("1.5")
    with pytest.raises(CorpusError):
        parse_key(str(MAX_KEY + 1))


def test_a_file_reads_whole_or_not_at_all(tmp_path) -> None:
    path = tmp_path / "keys.txt"
    path.write_text("# comment\n\n7\n-13\n", encoding="utf-8")
    assert load_keys(str(path)) == [7, -13]
    noise = tmp_path / "noise.txt"
    noise.write_text("7\nabc\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_keys(str(noise))
    with pytest.raises(CorpusError):
        load_keys(str(tmp_path / "missing.txt"))


def test_keys_write_back_the_way_they_read(tmp_path) -> None:
    path = tmp_path / "round.txt"
    write_keys([7, -13, 0], str(path))
    assert load_keys(str(path)) == [7, -13, 0]


def test_synthetic_is_distinct_and_seeded() -> None:
    first = synthetic(30, seed=4)
    again = synthetic(30, seed=4)
    other = synthetic(30, seed=5)
    assert first == again
    assert len(set(first)) == 30
    assert set(first) != set(other)
    with pytest.raises(CorpusError):
        synthetic(0)
    with pytest.raises(CorpusError):
        synthetic(10, span=4)


def test_a_snapshot_round_trips_through_json() -> None:
    snapshot = Snapshot((1, 2, 3), 7)
    assert Snapshot.loads(snapshot.dumps()) == snapshot
    for broken in ('{"keys": [1]}', '{"seed": 7}', "not json", "[]"):
        with pytest.raises(CorpusError):
            Snapshot.loads(broken)
