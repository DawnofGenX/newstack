"""The oracles: a plain sort and the property a heap array owes.

Every answer the heap gives must equal what this module answers on
the same keys. The drain order is `sorted(pushed)` with no
cleverness at all, and the shape question is the parent rule walked
slot by slot. The heap cannot grade its own homework from here.
"""

from __future__ import annotations

from typing import Any


def brute_drain(keys: Any) -> list[int]:
    """The keys in plain sorted order, the drain every pop storm owes."""
    return sorted(keys)


def parent_index(slot: int) -> int:
    """The parent of a slot in a zero-based array; -1 for the root."""
    return (slot - 1) // 2 if slot > 0 else -1


def child_indices(slot: int, size: int) -> tuple[int, ...]:
    """The live children of a slot; the walk's questions, never assumed."""
    left = 2 * slot + 1
    return tuple(index for index in (left, left + 1) if index < size)


def heap_breaks(array: list[int]) -> list[int]:
    """Every slot where the parent rule breaks: the shipped checker.

    The parent rides no higher than its children, so an honest array
    answers with an empty list. The walk is plain index arithmetic on
    the array itself — the checker the storm and the selftest both
    run after every operation.
    """
    return [
        slot
        for slot in range(len(array))
        if any(array[slot] > array[child] for child in child_indices(slot, len(array)))
    ]
