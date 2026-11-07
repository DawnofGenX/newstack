from __future__ import annotations

import pytest

from {{ package_name }}.brute import expose, naive_min, naive_sort
from {{ package_name }}.heap import FibonacciHeap


def test_the_sort_is_the_sort() -> None:
    keys = [5, -2, 0, 5, 99]
    assert naive_sort(keys) == sorted(keys)
    assert naive_min(keys) == min(keys)


def test_the_empty_pile_names_its_nothing() -> None:
    with pytest.raises(ValueError, match="empty"):
        naive_min([])


def test_the_walk_reads_links_not_answers() -> None:
    keys = [8, 3, 12, 3, -40]
    heap = FibonacciHeap(keys)
    assert expose(heap) == sorted(keys)
    for _ in range(2):
        heap.pop_min()
    assert expose(heap) == sorted(keys)[2:]


def test_the_walk_survives_a_decrease() -> None:
    heap = FibonacciHeap([50, 60, 70])
    handle = heap._handles[2]
    heap.decrease(handle, -1)
    assert expose(heap) == [-1, 50, 70]
