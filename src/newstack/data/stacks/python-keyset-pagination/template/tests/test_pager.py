"""Paging: cursors move, scans see everything, and a mutation cannot hide a row."""

from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }} import pager as subject
from {{ package_name }}.model import Order, Query
from {{ package_name }}.store import Store


def test_a_page_carries_a_next_cursor_when_there_is_more(store: Store) -> None:
    store.seed(30)
    first = subject.page(store, size=7)
    assert first.size == 7
    assert first.next_cursor is not None
    assert first.prev_cursor is None


def test_the_last_page_has_no_next_cursor(store: Store) -> None:
    store.seed(10)
    last = subject.page(store, size=10)
    assert last.size == 10
    assert last.next_cursor is None


def test_a_cursor_carries_the_rows_it_came_after(store: Store) -> None:
    store.seed(30)
    first = subject.page(store, size=7)
    assert first.next_cursor is not None
    decoded = subject.Cursor.decode(first.next_cursor)
    rows = store.fetch(Query(), size=100)[0]
    assert decoded.ident == rows[6].id


def test_a_scan_sees_every_row_once(store: Store) -> None:
    store.seed(30)
    expected = store.ordered_ids(Query())
    assert subject.scan(store, size=7) == expected
    assert subject.duplicates(subject.scan(store, size=7)) == []


def test_a_backward_page_walks_towards_the_start(store: Store) -> None:
    store.seed(30)
    expected = store.ordered_ids(Query())
    second = subject.page(store, size=7)
    forwards = subject.page(store, cursor=second.next_cursor, size=7)
    back = subject.page(store, cursor=forwards.prev_cursor, size=7, direction=subject.BACKWARD)
    assert back.ids == expected[:7]


def test_an_unknown_direction_is_refused(store: Store) -> None:
    with pytest.raises(subject.InputError, match="direction must be"):
        subject.page(store, size=5, direction="sideways")


def test_a_delete_behind_the_cursor_costs_offset_a_row(store: Store) -> None:
    store.seed(30)
    expected = store.ordered_ids(Query())
    first = subject.page(store, size=7)
    store.delete(first.ids[2])
    by_cursor = list(first.ids) + subject.walk(store, cursor=first.next_cursor, size=7)
    remaining = [ident for ident in expected if ident != first.ids[2]]
    assert subject.missing(by_cursor, remaining) == []
    assert subject.duplicates(by_cursor) == []


def test_duplicates_and_missing_report_what_they_found() -> None:
    assert subject.duplicates([1, 2, 2, 3, 3, 3]) == [2, 3]
    assert subject.missing([1, 3], [1, 2, 3, 4]) == [2, 4]
    assert subject.duplicates([]) == []


def test_a_page_with_a_forged_cursor_is_refused(store: Store) -> None:
    store.seed(10)
    cursor = subject.page(store, size=5).next_cursor
    assert cursor is not None
    with pytest.raises(subject.InputError, match="different query"):
        subject.page(store, Query(Order("title")), cursor=cursor, size=5)


def test_a_scan_stops_climbing_pages(tmp_path: Path) -> None:
    with Store(tmp_path / "small.db") as local:
        local.seed(3)
        assert subject.scan(local, size=2) == local.ordered_ids(Query())
