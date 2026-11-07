from __future__ import annotations

import contextlib

import pytest

from {{ package_name }}.ring import (
    RingBuffer,
    RingError,
)

PUSHED = list(range(12))


def test_fifo_order_holds_until_full() -> None:
    ring = RingBuffer(4, [1, 2, 3])
    assert ring.peek() == 1
    assert ring.pop() == 1
    assert len(ring) == 2
    assert ring.contents() == (2, 3)


def test_over_capacity_drops_exactly_the_oldest() -> None:
    ring = RingBuffer(3, [1, 2, 3])
    dropped = ring.push(4)
    assert dropped == 1
    assert ring.contents() == (2, 3, 4)
    assert ring.overwrites == 1
    assert ring.audit() == []


def test_the_cursor_never_leaves_the_ring() -> None:
    for capacity in (1, 2, 5, 16):
        ring = RingBuffer(capacity)
        for step in range(capacity * 4):
            ring.push(step)
            assert 0 <= ring.head < capacity
            assert 0 <= ring.tail < capacity
            if step % 2:
                with contextlib.suppress(RingError):
                    ring.pop()
                assert 0 <= ring.head < capacity


@pytest.mark.parametrize("capacity", (1, 3, 7))
def test_the_walk_is_recomputed_from_head_and_count(capacity: int) -> None:
    ring = RingBuffer(capacity)
    seats: list[int] = []
    for step in PUSHED:
        if ring.push(step) is not None:
            seats.pop(0)
        seats.append(step)
        assert list(ring.contents()) == seats
    assert ring.drain() == seats
    assert len(ring) == 0
    assert ring.head == 0


def test_empty_edges_stay_honest() -> None:
    ring = RingBuffer(4)
    assert len(ring) == 0
    assert ring.contents() == ()
    with pytest.raises(RingError):
        ring.pop()
    with pytest.raises(RingError):
        ring.peek()
    assert len(ring) == 0


def test_capacity_one_keeps_only_the_newest() -> None:
    lone = RingBuffer(1, [7, 8, 9])
    assert lone.peek() == 9
    assert lone.overwrites == 2
    assert lone.full
    assert lone.pop() == 9


def test_bad_capacity_and_noise_are_refused() -> None:
    with pytest.raises(RingError):
        RingBuffer(0)
    with pytest.raises(RingError):
        RingBuffer(2.5)  # type: ignore[arg-type]
    with pytest.raises(RingError):
        RingBuffer(-3)
    ring = RingBuffer(4)
    with pytest.raises(ValueError):
        ring.push(1.5)
    assert len(ring) == 0
