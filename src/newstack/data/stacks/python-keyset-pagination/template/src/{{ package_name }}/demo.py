"""The demonstration: two mutations that break LIMIT/OFFSET and cannot break a cursor.

Each scenario uses a fresh database and walks it twice, once by cursor and once
by offset, and the numbers printed are computed from the rows that came back.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .model import Order, Query
from .pager import duplicates, missing, page, walk
from .store import Store

SEED_COUNT = 30
SIZE = 7
ORDER = Query(Order("created_at", descending=False))
Mutate = Callable[[Store, list[int]], None]


@dataclass(frozen=True)
class Step:
    scenario: str
    keyset_seen: int
    keyset_skipped: int
    keyset_duplicated: int
    offset_seen: int
    offset_skipped: int
    offset_duplicated: int
    rows: int
    notes: tuple[str, ...]

    @property
    def keyset_clean(self) -> bool:
        return self.keyset_skipped == 0 and self.keyset_duplicated == 0

    @property
    def offset_broken(self) -> bool:
        return self.offset_skipped > 0 or self.offset_duplicated > 0

    def render(self) -> str:
        verdict = "cursor clean" if self.keyset_clean else "cursor BROKEN"
        tail = f"offset: skipped {self.offset_skipped}, repeated {self.offset_duplicated}"
        return f"{self.scenario:<30} {verdict:<14} {tail}"

    def lines(self) -> list[str]:
        return [
            f"rows walked: cursor {self.keyset_seen}, offset {self.offset_seen} of "
            f"{self.rows} that exist",
            *self.notes,
        ]


def _ordered_ids(store: Store) -> list[int]:
    return store.ordered_ids(ORDER)


def _walk(
    directory: Path, name: str, *, keyset: bool, mutate: Mutate
) -> tuple[list[int], list[int]]:
    stem = f"{name}-{'cursor' if keyset else 'offset'}.db"
    with Store(directory / stem) as store:
        store.seed(SEED_COUNT)
        snapshot = _ordered_ids(store)
        if keyset:
            first = page(store, ORDER, size=SIZE)
            mutate(store, list(first.ids))
            seen = list(first.ids)
            seen += walk(store, ORDER, cursor=first.next_cursor, size=SIZE)
        else:
            seen = []
            offset = 0
            touched = False
            while True:
                rows = store.fetch_offset(ORDER, offset=offset, size=SIZE)
                if not rows:
                    break
                if not touched:
                    mutate(store, [row.id for row in rows])
                    touched = True
                seen.extend(row.id for row in rows)
                offset += SIZE
    return seen, snapshot


def _scenario(
    directory: Path, name: str, mutate: Mutate, notes: tuple[str, ...]
) -> tuple[Step, list[int]]:
    key_seen, expected = _walk(directory, name, keyset=True, mutate=mutate)
    off_seen, _ = _walk(directory, name, keyset=False, mutate=mutate)
    key_missing = missing(key_seen, expected)
    off_missing = missing(off_seen, expected)
    step = Step(
        scenario=name,
        keyset_seen=len(key_seen),
        keyset_skipped=len(key_missing),
        keyset_duplicated=len(duplicates(key_seen)),
        offset_seen=len(off_seen),
        offset_skipped=len(off_missing),
        offset_duplicated=len(duplicates(off_seen)),
        rows=len(expected),
        notes=(
            f"offset never returned row(s) {off_missing or 'none'}",
            f"offset returned row(s) {duplicates(off_seen) or 'none'} twice",
            *notes,
        ),
    )
    return step, off_missing


def _deletion(directory: Path) -> Step:
    def mutate(store: Store, ids: list[int]) -> None:
        store.delete(ids[2])

    step, _ = _scenario(
        directory,
        "a row the client already saw is deleted",
        mutate,
        ("the deleted row was on page 1, so no later page can be blamed for missing it",),
    )
    return step


def _insertion(directory: Path) -> Step:
    def mutate(store: Store, ids: list[int]) -> None:
        del ids
        store.insert(9_000, 1_600_000_000, "inserted before the cursor")

    step, _ = _scenario(
        directory,
        "a row is inserted before the cursor",
        mutate,
        ("the new row sorts before the position, so a cursor rightly never shows it",),
    )
    return step


def run(directory: Path) -> tuple[Step, ...]:
    """Both scenarios; a caller can exit non-zero when either cursor walk is dirty."""
    return (_deletion(directory), _insertion(directory))
