from __future__ import annotations

from {{ package_name }}.brute import (
    drop_oldest_view,
    reference_drain,
    storm_reference,
)
from {{ package_name }}.ring import RingBuffer

PUSHED = list(range(12))


def test_the_view_is_the_visible_sequence() -> None:
    assert drop_oldest_view(3, PUSHED) == (9, 10, 11)
    assert drop_oldest_view(20, PUSHED) == tuple(PUSHED)


def test_the_drain_is_what_the_deque_hands_back() -> None:
    assert reference_drain(4, PUSHED) == [8, 9, 10, 11]
    assert reference_drain(2, []) == []


def test_the_storm_reference_answers_step_for_step() -> None:
    script = [("push", 1), ("push", 2), ("pop", None), ("push", 3), ("drain", None)]
    assert storm_reference(2, script) == [1, 2, 3]


def test_the_buffer_agrees_with_its_oracle() -> None:
    ring = RingBuffer(4, PUSHED)
    assert list(ring.drain()) == reference_drain(4, PUSHED)
