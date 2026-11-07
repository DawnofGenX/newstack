from __future__ import annotations

import pytest

from {{ package_name }}.heap import (
    FibonacciHeap,
    Handle,
    HeapError,
    degree_bound,
)


def test_quiet_heaps_drain_to_the_sort() -> None:
    for keys in ([1], [3, 1, 2], [-9, 0, 9, 0], list(range(64, 0, -1))):
        heap = FibonacciHeap(keys)
        assert [heap.pop_min() for _ in range(len(heap))] == sorted(keys)


def test_push_hands_back_a_live_handle() -> None:
    heap = FibonacciHeap()
    handle = heap.push(50)
    assert isinstance(handle, Handle)
    assert heap.peek() == 50
    assert len(heap) == 1


def test_decrease_lands_inside_heap_order() -> None:
    heap = FibonacciHeap()
    ledger: dict[int, int] = {}
    handles: dict[int, Handle] = {}
    for key in (400, 300, 200, 100, 50):
        handle = heap.push(key)
        ledger[handle.token] = key
        handles[handle.token] = handle
    for token, key in list(ledger.items()):
        heap.decrease(handles[token], key - 1000)
        ledger[token] -= 1000
    assert heap.keys() == sorted(ledger.values())
    assert heap.audit() == []


def test_a_deep_cascade_keeps_the_forest_ordered() -> None:
    heap = FibonacciHeap()
    handles = [heap.push(key) for key in range(1, 60)]
    for handle in handles:
        heap.decrease(handle, -handle.token)
    assert heap.keys() == sorted(-h.token for h in handles)
    assert heap.invariant()


def test_degrees_stay_under_the_documented_bound() -> None:
    heap = FibonacciHeap(range(200))
    for _ in range(150):
        heap.pop_min()
    bound = degree_bound(max(len(heap), 1))
    assert all(degree <= bound for degree in heap.degrees())


def test_an_increase_is_refused_by_name() -> None:
    heap = FibonacciHeap([5])
    handle = next(iter(heap._handles.values()))
    with pytest.raises(HeapError, match="not a decrease"):
        heap.decrease(handle, 6)
    assert heap.keys() == [5]


def test_equal_key_decrease_is_quiet() -> None:
    heap = FibonacciHeap([5])
    handle = next(iter(heap._handles.values()))
    heap.decrease(handle, 5)
    assert heap.keys() == [5]


def test_a_stale_handle_is_refused() -> None:
    heap = FibonacciHeap()
    handle = heap.push(1)
    heap.pop_min()
    with pytest.raises(HeapError, match="stale"):
        heap.decrease(handle, 0)


def test_empty_and_single_answer_the_edges() -> None:
    bare = FibonacciHeap()
    assert bare.keys() == []
    assert bare.invariant()
    with pytest.raises(HeapError, match="empty"):
        bare.peek()
    with pytest.raises(HeapError, match="empty"):
        bare.pop_min()
    one = FibonacciHeap([7])
    assert one.peek() == 7
    assert one.pop_min() == 7
    assert len(one) == 0


def test_duplicated_keys_stay_distinct_items() -> None:
    heap = FibonacciHeap([2, 2, 2])
    assert len(heap) == 3
    assert heap.keys() == [2, 2, 2]
