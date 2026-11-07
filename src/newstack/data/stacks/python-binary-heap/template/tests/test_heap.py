from __future__ import annotations

import random

import pytest

from {{ package_name }}.corpus import (
    synthetic,
)
from {{ package_name }}.heap import (
    HeapError,
    MinHeap,
)
from {{ package_name }}.oracle import (
    brute_drain,
)

SEEDS = (7, 23, 91, 1009)
KEYSETS = ((1, 2, 3, 4, 5), (5, 3, 8, 1, 4, 9, 2), (-7, 0, 7))


def test_the_drain_is_the_plain_sort() -> None:
    for keys in KEYSETS:
        assert MinHeap(keys).drain() == sorted(keys)
    for seed in SEEDS:
        keys = synthetic(24, seed=seed)
        assert MinHeap(keys).drain() == sorted(keys)


def test_the_parent_rule_holds_after_every_operation() -> None:
    for seed in SEEDS:
        rng = random.Random(seed)
        pool = synthetic(32, seed=seed)
        heap = MinHeap()
        for _ in range(160):
            if rng.random() < 0.6:
                heap.push(rng.choice(pool))
            elif heap:
                heap.pop()
            assert heap.breaks() == []


def test_the_head_is_the_minimum_of_the_live_bag() -> None:
    for seed in SEEDS:
        keys = synthetic(20, seed=seed)
        heap = MinHeap(keys)
        live = list(keys)
        while live:
            assert heap.peek() == min(live)
            live.remove(heap.pop())
        assert len(heap) == 0


def test_pop_of_nothing_is_refused() -> None:
    heap = MinHeap()
    with pytest.raises(HeapError):
        heap.pop()
    with pytest.raises(HeapError):
        heap.peek()
    assert len(heap) == 0


def test_repeats_keep_every_seat() -> None:
    heap = MinHeap([4, 4, 1, 4])
    assert heap.drain() == [1, 4, 4, 4]
    assert len(heap) == 0


def test_an_emptied_heap_takes_keys_again() -> None:
    heap = MinHeap([9])
    assert heap.pop() == 9
    heap.push(2)
    heap.push(1)
    assert heap.peek() == 1
    assert heap.drain() == [1, 2]


def test_mixed_storms_drain_the_sort() -> None:
    for seed in SEEDS:
        rng = random.Random(seed)
        pool = synthetic(48, seed=seed)
        heap = MinHeap()
        live: list[int] = []
        for _ in range(160):
            if rng.random() < 0.55 or not live:
                key = rng.choice(pool)
                heap.push(key)
                live.append(key)
            else:
                got = heap.pop()
                live.remove(got)
            assert heap.breaks() == []
            if live:
                assert heap.peek() == min(live)
            else:
                assert len(heap) == 0
        assert heap.drain() == brute_drain(live)
