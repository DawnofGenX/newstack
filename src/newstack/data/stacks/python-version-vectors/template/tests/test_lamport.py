"""The total order, and the unrelated local work it cannot see."""

import pytest

from {{ package_name }} import lamport as subject


def test_a_tick_moves_forward():
    clock = subject.LamportClock("a")
    assert clock.tick().time == 1
    assert clock.tick().time == 2
    assert clock.ticks == 2


def test_a_stamp_prints_its_time_and_node():
    assert subject.Stamp(7, "a").text() == "0007@a"


def test_a_receive_is_after_the_message_and_after_local_work():
    clock = subject.busy("b", 5)
    received = clock.receive(subject.Stamp(3, "a"))
    assert received.time == 6
    assert received.node == "b"


def test_the_total_order_sorts_by_time_then_node():
    events = [subject.Event("b", subject.Stamp(2, "b")), subject.Event("a", subject.Stamp(1, "a"))]
    assert [event.name for event in subject.order(events)] == ["a", "b"]


def test_two_stamps_at_the_same_time_are_broken_by_name():
    events = [
        subject.Event("late", subject.Stamp(3, "z")),
        subject.Event("early", subject.Stamp(3, "a")),
    ]
    assert [event.name for event in subject.order(events)] == ["early", "late"]


def test_unrelated_local_work_flips_the_order_of_two_concurrent_events():
    draft = subject.Event("draft", subject.busy("a", 2).tick())
    idle = subject.Event("comment", subject.LamportClock("b").tick())
    busy = subject.Event("comment", subject.busy("b", 5).tick())
    assert subject.precedes(idle, draft)
    assert subject.precedes(draft, busy)


def test_precedes_is_antisymmetric_for_two_stamps():
    left = subject.Event("left", subject.Stamp(1, "a"))
    right = subject.Event("right", subject.Stamp(2, "a"))
    assert subject.precedes(left, right)
    assert not subject.precedes(right, left)


def test_a_busy_clock_counts_its_ticks():
    assert subject.busy("c", 4).ticks == 4


def test_a_negative_tick_count_is_refused():
    with pytest.raises(subject.LamportError, match="whole number"):
        subject.busy("a", -1)


def test_an_empty_order_is_refused():
    with pytest.raises(subject.LamportError, match="no order of no events"):
        subject.order([])


def test_a_negative_stamp_is_refused():
    with pytest.raises(subject.LamportError, match="negative"):
        subject.Stamp(-1, "a")


def test_a_stamp_needs_a_node():
    with pytest.raises(subject.LamportError, match="node name"):
        subject.Stamp(1, "")


def test_an_event_prints_its_note_only_when_it_has_one():
    assert subject.Event("x", subject.Stamp(1, "a")).text() == "0001@a  x"
    assert subject.Event("x", subject.Stamp(1, "a"), "note").text().endswith("note")
