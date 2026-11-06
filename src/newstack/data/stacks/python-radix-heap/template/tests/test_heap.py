from __future__ import annotations

import pytest

from {{ package_name }}.heap import (
    BUCKETS,
    HeapError,
    RadixHeap,
    bucket_of,
)

KEYS = [0, 4, 15, 17, 30, 63, 64, 100, 255, 256, 500, 900, 1023, 2047, 4095]


def filled() -> RadixHeap:
    heap = RadixHeap()
    for index, key in enumerate(KEYS):
        heap.push(key, index)
    return heap


def test_a_seat_is_a_bit_length_not_a_comparison() -> None:
    assert bucket_of(0, 0) == 0
    assert bucket_of(8, 0) == 4
    assert bucket_of(63, 64) == 7
    assert bucket_of(17, 17) == 0


def test_draining_is_the_sorted_corpus() -> None:
    heap = filled()
    assert list(heap.pop_all()) == sorted(KEYS)
    assert len(heap) == 0
    assert not heap


def test_the_count_is_the_count() -> None:
    heap = filled()
    assert len(heap) == len(KEYS)


def test_every_key_sits_at_its_bit_length_from_base_bucket() -> None:
    heap = filled()
    for index, bucket in enumerate(heap._buckets):
        for key, _ in bucket:
            assert bucket_of(key, heap.base) == index
    for _ in range(4):
        heap.pop()
        assert heap.invariant()
        for index, bucket in enumerate(heap._buckets):
            for key, _ in bucket:
                assert bucket_of(key, heap.base) == index


def test_the_window_walks_forward_and_drops_nothing_behind() -> None:
    heap = filled()
    walked = [heap.pop()[0] for _ in range(6)]
    assert walked == sorted(KEYS[:6])
    assert heap.base == walked[-1]
    assert all(key >= heap.base for key, _ in heap.entries())


def test_a_pop_from_an_empty_heap_is_refused() -> None:
    with pytest.raises(HeapError):
        RadixHeap().pop()


def test_a_key_below_the_floor_has_no_bucket() -> None:
    with pytest.raises(HeapError):
        RadixHeap().push(-1)


def test_a_wide_key_has_no_bucket() -> None:
    with pytest.raises(HeapError):
        RadixHeap().push((1 << 65) + 7)
    assert BUCKETS == 65


def test_a_refile_never_drops_a_key_equal_to_the_window() -> None:
    heap = RadixHeap()
    for key in (9, 9, 70):
        heap.push(key, key)
    heap.pop()
    assert heap.entries() == [(9, 9), (70, 70)]
    assert heap.invariant()


def test_a_backwards_push_buys_one_rebuild_never_a_wrong_answer() -> None:
    heap = RadixHeap()
    for key in (5, 9, 14):
        heap.push(key, None)
    heap.pop()
    edit = heap.push(3, "three")
    assert edit.rebuilt
    assert heap.rebuilds == 1
    assert heap.invariant()
    assert list(heap.pop_all()) == [3, 9, 14]


def test_a_rebuild_preserves_the_answer() -> None:
    heap = filled()
    for _ in range(6):
        heap.pop()
    heap.rebuild()
    assert heap.invariant()
    assert list(heap.pop_all()) == sorted(KEYS)[6:]


def test_peek_names_the_next_pop_without_paying_for_it() -> None:
    heap = filled()
    assert heap.peek()[0] == min(KEYS)
    assert len(heap) == len(KEYS)
    assert heap.pop()[0] == min(KEYS)


def test_the_edit_line_names_the_op_and_the_seat() -> None:
    edit = RadixHeap().push(9, None)
    assert edit.op == "push"
    assert edit.bucket == 4
    assert "push bucket 4" in edit.line()


def test_stats_describe_the_window_without_lying() -> None:
    stats = filled().stats()
    assert stats["size"] == len(KEYS)
    assert stats["base"] == 0
    assert stats["rebuilds"] == 0
    assert stats["invariant"]
    assert sum(stats["buckets"]) == len(KEYS)
    assert len(stats["buckets"]) == BUCKETS


def test_lines_describe_the_shape_without_lying() -> None:
    rows = filled().lines()
    assert rows[0].startswith(f"size {len(KEYS)} base 0 rebuilds 0")
    assert any(row.strip().startswith("bucket") for row in rows)
