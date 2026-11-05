"""The order, the query fingerprint, and the cursor round trip."""

from __future__ import annotations

import base64
import json

import pytest

from {{ package_name }} import model as subject


def test_an_order_sorts_by_key_then_id() -> None:
    assert subject.Order().columns() == "created_at ASC, id ASC"
    assert subject.Order("title", True).columns() == "title DESC, id DESC"


def test_the_comparison_matches_the_direction() -> None:
    assert subject.Order().comparison() == "(created_at, id) > (?, ?)"
    assert subject.Order("title", True).comparison() == "(title, id) < (?, ?)"


def test_an_unknown_sort_key_is_refused() -> None:
    with pytest.raises(subject.InputError, match="unknown sort key"):
        subject.Order("body")


def test_the_fingerprint_changes_with_the_query() -> None:
    first = subject.Query(subject.Order("created_at", False), "note")
    second = subject.Query(subject.Order("created_at", True), "note")
    third = subject.Query(subject.Order("created_at", False), "other")
    assert first.fingerprint != second.fingerprint
    assert first.fingerprint != third.fingerprint
    assert len(first.fingerprint) == 12


def test_the_fingerprint_is_stable() -> None:
    assert subject.Query().fingerprint == subject.Query().fingerprint


def test_a_cursor_round_trips() -> None:
    cursor = subject.Cursor(1_700_000_004, 12, "abc123abc123")
    assert subject.Cursor.decode(cursor.encode()) == cursor


def test_a_cursor_is_opaque_and_unpadded() -> None:
    text = subject.Cursor(1_700_000_004, 12, "abc123abc123").encode()
    assert "=" not in text
    assert "sort" not in text
    assert subject.Cursor.decode(text).ident == 12


def test_a_cursor_bound_to_another_query_is_refused() -> None:
    query = subject.Query(subject.Order("created_at", False), "note")
    cursor = subject.Cursor(1, 2, query.fingerprint)
    cursor.check(query)
    with pytest.raises(subject.InputError, match="different query"):
        cursor.check(subject.Query(subject.Order("title"), "note"))


def payload(**members: object) -> str:
    return base64.urlsafe_b64encode(json.dumps(members).encode()).decode().rstrip("=")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("", "non-empty"),
        ("not base64 !!!", "base64url"),
        (base64.urlsafe_b64encode(b"nonsense").decode().rstrip("="), "not JSON"),
        (payload(sort=1), "missing"),
        (payload(sort=1, id="x", query="abc"), "id must be an integer"),
        (payload(**{"v": 9, "sort": 1, "id": 1, "query": "abc"}), "version"),
        (payload(**{"sort": 1, "id": 1, "query": 5}), "fingerprint string"),
    ],
)
def test_a_bad_cursor_is_refused(text: str, message: str) -> None:
    with pytest.raises(subject.InputError, match=message):
        subject.Cursor.decode(text)


def test_a_page_reports_its_ids() -> None:
    page = subject.Page(({"id": 3}, {"id": 4}), "next", None, "abc")
    assert page.ids == [3, 4]
    assert page.size == 2
    assert page.as_dict()["query"] == "abc"
