from __future__ import annotations

import pytest

from {{ package_name }} import clock as subject
from {{ package_name }}.stamp import Stamp

ManualWall = subject.ManualWall
HybridClock = subject.HybridClock


def make(start: int = 1_000) -> tuple[subject.ManualWall, subject.HybridClock]:
    wall = ManualWall(start)
    return wall, HybridClock("a", wall_ms=wall.now)


def test_local_events_increase_with_an_advancing_wall() -> None:
    wall, clock = make()
    first = clock.now()
    wall.advance(5)
    second = clock.now()
    assert first < second
    assert second.physical_ms == 1_005
    assert second.logical == 0


def test_local_events_increase_inside_one_millisecond() -> None:
    _, clock = make()
    first = clock.now()
    second = clock.now()
    assert first.physical_ms == second.physical_ms
    assert second.logical == first.logical + 1


def test_a_backwards_wall_still_increases_the_stamp() -> None:
    wall, clock = make()
    first = clock.now()
    wall.set(600)
    second = clock.now()
    assert second > first
    assert second.physical_ms == first.physical_ms


def test_a_backwards_wall_is_not_a_new_millisecond() -> None:
    wall, clock = make()
    clock.now()
    wall.set(600)
    stamp = clock.now()
    assert stamp.physical_ms == 1_000
    assert stamp.logical >= 1


def test_receiving_a_future_stamp_moves_the_clock_past_it() -> None:
    _, clock = make()
    remote = Stamp(5_000, 0, "b")
    received = clock.receive(remote)
    assert received > remote
    assert received.physical_ms == 5_000
    assert received.logical == 1


def test_receiving_an_older_stamp_only_bumps_the_counter() -> None:
    wall, clock = make()
    clock.now()
    wall.advance(10)
    clock.now()
    received = clock.receive(Stamp(1_000, 0, "b"))
    assert received.physical_ms == 1_010
    assert received.logical == 1


def test_receiving_from_a_clock_behind_keeps_our_physical_time() -> None:
    _, clock = make()
    clock.now()
    received = clock.receive(Stamp(900, 4, "b"))
    assert received.physical_ms == 1_000
    assert received.logical == 1


def test_the_wall_clock_overtaking_both_resets_the_counter() -> None:
    wall, clock = make()
    clock.receive(Stamp(5_000, 3, "b"))
    wall.set(6_000)  # the wall catches up and passes the remote
    stamp = clock.now()
    assert stamp.physical_ms == 6_000
    assert stamp.logical == 0


def test_skew_is_measured_against_the_wall() -> None:
    _, clock = make()
    clock.receive(Stamp(1_500, 0, "b"))
    assert clock.skew_ms() == 500
    assert clock.is_drifting()


def test_a_bound_turns_skew_into_a_refusal() -> None:
    wall = ManualWall(1_000)
    clock = HybridClock("a", wall_ms=wall.now, max_skew_ms=400)
    clock.receive(Stamp(1_500, 0, "b"))
    with pytest.raises(subject.ClockError, match="400 ms bound"):
        clock.check_skew()


def test_a_skew_inside_the_bound_is_accepted() -> None:
    wall = ManualWall(1_000)
    clock = HybridClock("a", wall_ms=wall.now, max_skew_ms=600)
    clock.receive(Stamp(1_500, 0, "b"))
    clock.check_skew()


def test_a_clock_needs_a_node() -> None:
    with pytest.raises(subject.ClockError, match="node name"):
        HybridClock("", wall_ms=lambda: 0)


def test_a_negative_skew_bound_is_refused() -> None:
    with pytest.raises(subject.ClockError, match="negative"):
        HybridClock("a", wall_ms=lambda: 0, max_skew_ms=-1)


def test_receiving_something_that_is_not_a_stamp_is_refused() -> None:
    _, clock = make()
    with pytest.raises(subject.ClockError, match="takes a Stamp"):
        clock.receive(1_000)  # type: ignore[arg-type]


def test_the_wall_cannot_be_advanced_backwards() -> None:
    wall = ManualWall(1_000)
    with pytest.raises(subject.ClockError, match="backwards"):
        wall.advance(-1)
