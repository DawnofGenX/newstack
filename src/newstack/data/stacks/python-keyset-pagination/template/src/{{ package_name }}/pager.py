"""Paging itself: cursors in, pages out, and a scan that proves nothing was missed.

A page is fetched with `size + 1` rows so "is there more?" is answered by the
query instead of a second `COUNT(*)`, which would answer a different question —
the count at a different moment.
"""

from __future__ import annotations

from .model import Cursor, InputError, Page, Query
from .store import DEFAULT_SIZE, Store

FORWARD = "forward"
BACKWARD = "backward"
DIRECTIONS = (FORWARD, BACKWARD)


def _cursor_for(row: dict[str, object], query: Query) -> str:
    order = query.order
    value = row["created_at"] if order.key == "created_at" else row["title"]
    return Cursor(value, int(row["id"]), query.fingerprint).encode()


def page(
    store: Store,
    query: Query | None = None,
    *,
    cursor: str | None = None,
    size: int = DEFAULT_SIZE,
    direction: str = FORWARD,
) -> Page:
    """One page. `next_cursor` is None only when the query has no further rows."""
    spec = query or Query()
    if direction not in DIRECTIONS:
        raise InputError(f"direction must be forward or backward, got {direction!r}")
    backwards = direction == BACKWARD
    decoded = None if cursor is None else Cursor.decode(cursor)
    rows, more = store.fetch(spec, cursor=decoded, size=size, backwards=backwards)
    as_dicts = [row.as_dict() for row in rows]
    next_cursor = None
    prev_cursor = None
    if more and as_dicts:
        boundary = as_dicts[0] if backwards else as_dicts[-1]
        next_cursor = _cursor_for(boundary, spec)
    if cursor is not None and as_dicts:
        prev_cursor = _cursor_for(as_dicts[0], spec)
    return Page(tuple(as_dicts), next_cursor, prev_cursor, spec.fingerprint)


def scan(
    store: Store, query: Query | None = None, *, size: int = DEFAULT_SIZE, limit: int = 10_000
) -> list[int]:
    """Walk every page and return the ids in order. Used by tests, and by the CLI's `scan`."""
    seen: list[int] = []
    cursor: str | None = None
    for _ in range(limit):
        current = page(store, query, cursor=cursor, size=size)
        seen.extend(current.ids)
        cursor = current.next_cursor
        if cursor is None:
            return seen
    raise InputError(f"scan gave up after {limit} pages; is the cursor moving?")


def walk(
    store: Store,
    query: Query | None = None,
    *,
    cursor: str | None = None,
    size: int = DEFAULT_SIZE,
    limit: int = 10_000,
) -> list[int]:
    """Continue a scan from a cursor somebody else already printed."""
    seen: list[int] = []
    for _ in range(limit):
        current = page(store, query, cursor=cursor, size=size)
        seen.extend(current.ids)
        cursor = current.next_cursor
        if cursor is None:
            return seen
    raise InputError(f"walk gave up after {limit} pages; is the cursor moving?")


def duplicates(ids: list[int]) -> list[int]:
    """Ids seen more than once, in the order they were first repeated."""
    counts: dict[int, int] = {}
    for ident in ids:
        counts[ident] = counts.get(ident, 0) + 1
    return [ident for ident, count in counts.items() if count > 1]


def missing(seen: list[int], expected: list[int]) -> list[int]:
    """Rows that exist but were never returned."""
    returned = set(seen)
    return [ident for ident in expected if ident not in returned]
