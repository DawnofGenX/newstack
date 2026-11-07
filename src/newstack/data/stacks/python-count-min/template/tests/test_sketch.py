from __future__ import annotations

import pytest

from {{ package_name }}.sketch import (
    CountMinSketch,
    SketchError,
)

EVENTS = [(7, 3), (7, 1), (199, 2), (0, 4), (64, 1)]


def _sketch(events: list[tuple[int, int]] | None = None) -> CountMinSketch:
    sketch = CountMinSketch()
    for key, n in events if events is not None else EVENTS:
        sketch.add(key, n)
    return sketch


def test_an_empty_sketch_counts_zero() -> None:
    bare = CountMinSketch()
    assert bare.count(7) == 0
    assert bare.keys() == []
    assert bare.total == 0
    assert bare.audit() == []


def test_the_min_never_dips_under_the_truth() -> None:
    sketch = _sketch()
    assert sketch.count(7) >= sketch.true_count(7)
    assert sketch.count(199) >= sketch.true_count(199)
    assert sketch.count(1) >= sketch.true_count(1)


def test_the_shipped_grid_answers_the_ledger_exactly() -> None:
    sketch = _sketch()
    for key, _n in EVENTS:
        assert sketch.count(key) == sketch.true_count(key)
    assert sketch.true_count(7) == 4
    assert sketch.total == 11


def test_the_answer_is_the_min_of_the_rows() -> None:
    narrow = CountMinSketch(width=48, multipliers=(3, 5, 7, 11, 13))
    narrow.add(1, 2)
    narrow.add(17, 3)
    rows = [
        narrow.rows[row][narrow.cells_of(1)[row]] for row in range(narrow.depth)
    ]
    assert narrow.count(1) == min(rows)
    assert narrow.count(1) == 2
    assert max(rows) > narrow.count(1)


def test_a_replay_matches_its_twin() -> None:
    first, second = _sketch(), _sketch()
    assert first.rows == second.rows
    assert first.keys() == second.keys()


def test_tracked_keys_come_back_ordered() -> None:
    assert _sketch().keys() == [0, 7, 64, 199]


def test_the_audit_catches_a_grid_that_undercounts() -> None:
    sketch = _sketch([(11, 3)])
    cell = sketch.cells_of(11)[0]
    sketch.rows[0][cell] -= 1
    assert sketch.audit()
    sketch.rows[0][cell] += 1
    assert sketch.audit() == []


def test_noise_is_refused_and_changes_nothing() -> None:
    from {{ package_name }}.keys import KeysError

    sketch = _sketch([(11, 3)])
    with pytest.raises(KeysError):
        sketch.add(300, 1)
    with pytest.raises(SketchError):
        sketch.add(11, 0)
    with pytest.raises(SketchError):
        sketch.add(11, -2)
    with pytest.raises(SketchError):
        sketch.add(11, 1.5)
    assert sketch.count(11) == 3


def test_a_shape_without_rows_is_refused() -> None:
    with pytest.raises(SketchError):
        CountMinSketch(width=0)
    with pytest.raises(SketchError):
        CountMinSketch(depth=3, multipliers=(3, 5))
    with pytest.raises(SketchError):
        CountMinSketch(multipliers=(2, 5, 7, 11, 13))


def test_the_report_names_the_shape() -> None:
    report = _sketch().report()
    assert report["width"] == 256
    assert report["depth"] == 5
    assert report["tracked"] == 4
    assert report["total"] == 11
