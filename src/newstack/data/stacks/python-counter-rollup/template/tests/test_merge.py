from __future__ import annotations

import json
from pathlib import Path

import pytest
from support import MICROSECONDS, readings

from {{ package_name }} import merge as subject
from {{ package_name }} import model
from {{ package_name }} import rollup as roller

WIDTH = 10 * MICROSECONDS


def _piece(total: int, shard: str = "a") -> model.Rollup:
    return roller.rollup(readings([(0, 0), (10, total)]), WIDTH, name="r", shard=shard)[0]


def test_an_exact_repeat_is_dropped() -> None:
    piece = _piece(100)
    result = subject.merge([piece, piece])
    assert len(result.rollups) == 1
    assert result.repeated == 1
    assert result.rollups[0].total == 100


def test_a_repeat_that_disagrees_is_refused() -> None:
    with pytest.raises(model.Conflict, match="one of them is wrong"):
        subject.merge([_piece(100), _piece(101)])


def test_different_shards_are_different_rows() -> None:
    result = subject.merge([_piece(100, "a"), _piece(40, "b")])
    assert [(piece.shard, piece.total) for piece in result.rollups] == [("a", 100), ("b", 40)]


def test_combining_adds_the_shards_and_unions_their_coverage() -> None:
    pieces = [_piece(100, "a"), _piece(40, "b")]
    combined = subject.combine(pieces)
    assert len(combined) == 1
    assert combined[0].total == 140
    assert combined[0].shard == "*"
    assert combined[0].first_us == 0
    assert combined[0].last_us == 10 * MICROSECONDS


def test_merging_keeps_the_windows_in_time_order() -> None:
    late = roller.rollup(readings([(10, 0), (20, 5)]), WIDTH, name="r")[0]
    early = roller.rollup(readings([(0, 0), (10, 7)]), WIDTH, name="r")[0]
    result = subject.merge([late, early])
    assert [piece.window.start_us for piece in result.rollups] == sorted(
        piece.window.start_us for piece in result.rollups
    )


def test_a_rollup_round_trips_through_json(tmp_path: Path) -> None:
    piece = _piece(30)
    path = tmp_path / "rollups.json"
    path.write_text(json.dumps([piece.as_dict()]), encoding="utf-8")
    assert subject.load(path) == [piece]


def test_a_bad_rollup_file_is_named_not_crashed(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(subject.RollupError, match="does not hold a list"):
        subject.load(path)
    missing = tmp_path / "missing.json"
    with pytest.raises(subject.RollupError, match="cannot read"):
        subject.load(missing)


def test_a_payload_without_a_window_is_refused() -> None:
    with pytest.raises(subject.RollupError, match="has no window object"):
        subject.parse_rollup({"name": "r"}, "entry 0")
    with pytest.raises(subject.RollupError, match="is missing 'shard'"):
        subject.parse_rollup({"name": "r", "window": {"start_us": 0, "end_us": 1}}, "entry 1")
