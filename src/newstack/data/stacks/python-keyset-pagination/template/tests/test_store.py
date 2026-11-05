"""The database: deterministic seeding, one query shape, pages that do not overlap."""

from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }} import store as subject
from {{ package_name }}.model import Order, Query


def test_seeding_is_deterministic(tmp_path: Path) -> None:
    with subject.Store(tmp_path / "one.db") as one:
        first = one.seed(20)
    with subject.Store(tmp_path / "two.db") as two:
        second = two.seed(20)
    assert first == second
    assert len(set(first)) == 20


def test_seeding_refuses_an_empty_population(store: subject.Store) -> None:
    with pytest.raises(ValueError, match="at least one item"):
        store.seed(0)


def test_timestamps_tie_so_the_id_has_to_break_the_tie(store: subject.Store) -> None:
    store.seed(12)
    rows = store.fetch(Query(), size=100)[0]
    timestamps = [row.created_at for row in rows]
    assert len(set(timestamps)) < len(timestamps)


def test_a_page_does_not_overlap_the_next(store: subject.Store) -> None:
    store.seed(30)
    from {{ package_name }}.pager import page

    first = page(store, size=7)
    second = page(store, cursor=first.next_cursor, size=7)
    assert set(first.ids) & set(second.ids) == set()


def test_the_order_is_the_key_then_the_id(store: subject.Store) -> None:
    store.seed(30)
    rows = store.fetch(Query(), size=100)[0]
    pairs = [(row.created_at, row.id) for row in rows]
    assert pairs == sorted(pairs)


def test_a_descending_order_reverses_both_columns(store: subject.Store) -> None:
    store.seed(30)
    rows = store.fetch(Query(Order("created_at", True)), size=100)[0]
    pairs = [(row.created_at, row.id) for row in rows]
    assert pairs == sorted(pairs, reverse=True)


def test_a_prefix_filter_narrows_the_population(store: subject.Store) -> None:
    store.seed(30)
    assert store.count(Query(title_prefix="note 01")) == 10


def test_a_full_page_says_there_is_more(store: subject.Store) -> None:
    store.seed(30)
    rows, more = store.fetch(Query(), size=29)
    assert len(rows) == 29
    assert more is True


def test_the_last_page_says_there_is_not(store: subject.Store) -> None:
    store.seed(30)
    rows, more = store.fetch(Query(), size=30)
    assert len(rows) == 30
    assert more is False


@pytest.mark.parametrize("size", [0, -1, 10_000])
def test_a_page_size_outside_the_range_is_refused(store: subject.Store, size: int) -> None:
    with pytest.raises(ValueError, match="size must be"):
        store.fetch(Query(), size=size)


def test_offset_paging_is_available_for_the_demo(store: subject.Store) -> None:
    store.seed(30)
    rows = store.fetch_offset(Query(), offset=0, size=7)
    assert [row.id for row in rows] == store.ordered_ids(Query())[:7]
    with pytest.raises(ValueError, match="negative"):
        store.fetch_offset(Query(), offset=-1, size=7)


def test_a_bad_row_is_refused(store: subject.Store) -> None:
    with pytest.raises(ValueError, match="title"):
        store.insert(1, 1_700_000_000, "")
    with pytest.raises(ValueError, match="id must be an integer"):
        store.insert("1", 1_700_000_000, "x")


def test_an_openable_path_error_is_wrapped(tmp_path: Path) -> None:
    with pytest.raises(subject.StoreError, match="cannot open"):
        subject.Store(tmp_path / "missing" / "dir" / "db.sqlite")
