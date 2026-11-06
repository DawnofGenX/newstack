"""The sequence, the clock, and what a backwards step costs."""

import pytest

from {{ package_name }} import generator as subject
from {{ package_name }} import layout


def clock_at(offset=0):
    return subject.ManualClock(layout.EPOCH_MS + offset)


def test_two_identifiers_in_one_millisecond_differ():
    worker = subject.SnowflakeGenerator(1, clock=clock_at())
    assert worker.next_id() != worker.next_id()


def test_the_sequence_advances_within_a_millisecond():
    worker = subject.SnowflakeGenerator(1, clock=clock_at())
    values = [worker.next_id() for _ in range(3)]
    assert [layout.decode(value).sequence for value in values] == [0, 1, 2]


def test_a_new_millisecond_restarts_the_sequence():
    clock = clock_at()
    worker = subject.SnowflakeGenerator(1, clock=clock)
    worker.next_id()
    worker.next_id()
    clock.advance(1)
    assert layout.decode(worker.next_id()).sequence == 0


def test_one_millisecond_holds_the_whole_sequence():
    clock = clock_at()
    worker = subject.SnowflakeGenerator(1, clock=clock)
    values = [worker.next_id() for _ in range(layout.IDS_PER_MS + 1)]
    assert sum(1 for value in values if layout.decode(value).relative_ms == 0) == layout.IDS_PER_MS
    assert worker.waits == 1


def test_identifiers_stay_increasing_across_a_wait():
    clock = clock_at()
    worker = subject.SnowflakeGenerator(1, clock=clock)
    values = [worker.next_id() for _ in range(layout.IDS_PER_MS + 10)]
    assert values == sorted(values)


def test_a_backwards_clock_is_refused_by_default():
    clock = clock_at(1_000)
    worker = subject.SnowflakeGenerator(1, clock=clock)
    worker.next_id()
    clock.set(layout.EPOCH_MS + 990)
    with pytest.raises(subject.ClockError, match="moved back"):
        worker.next_id()


def test_holding_keeps_the_last_millisecond():
    clock = clock_at(1_000)
    worker = subject.SnowflakeGenerator(1, clock=clock, on_rollback="hold")
    worker.next_id()
    clock.set(layout.EPOCH_MS + 990)
    values = [worker.next_id() for _ in range(3)]
    assert {layout.decode(value).relative_ms for value in values} == {1_000}
    assert [layout.decode(value).sequence for value in values] == [1, 2, 3]


class Frozen:
    """A clock that never moves, so the generator cannot wait its way out."""

    def __init__(self, now_ms):
        self._now = now_ms

    def now_ms(self):
        return self._now

    def set(self, now_ms):
        self._now = now_ms

    def wait_until(self, now_ms):
        return False


def test_the_held_sequence_is_a_finite_budget_when_time_cannot_pass():
    clock = Frozen(layout.EPOCH_MS + 1_000)
    worker = subject.SnowflakeGenerator(1, clock=clock, on_rollback="hold")
    worker.next_id()
    clock.set(layout.EPOCH_MS + 990)
    with pytest.raises(subject.ClockError, match="whole sequence"):
        for _ in range(layout.MAX_SEQUENCE + 2):
            worker.next_id()


def test_holding_waits_when_the_clock_can_move():
    clock = clock_at(1_000)
    worker = subject.SnowflakeGenerator(1, clock=clock, on_rollback="hold")
    worker.next_id()
    clock.set(layout.EPOCH_MS + 990)
    for _ in range(layout.MAX_SEQUENCE + 1):
        worker.next_id()
    assert worker.waits == 1


def test_an_unknown_rollback_strategy_is_refused():
    with pytest.raises(subject.ClockError, match="on_rollback"):
        subject.SnowflakeGenerator(1, on_rollback="ignore")


def test_a_clock_that_cannot_move_forward_refuses_the_overflow():
    class Stuck:
        def now_ms(self):
            return layout.EPOCH_MS

        def wait_until(self, now_ms):
            return False

    worker = subject.SnowflakeGenerator(1, clock=Stuck())
    with pytest.raises(subject.ClockError, match="cannot move forward"):
        for _ in range(layout.IDS_PER_MS + 1):
            worker.next_id()


def test_the_stats_count_what_happened():
    clock = clock_at()
    worker = subject.SnowflakeGenerator(2, clock=clock)
    worker.next_id()
    assert worker.stats() == {"worker": 2, "issued": 1, "waits": 0, "holds": 0}


def test_generate_issues_the_requested_count():
    values = subject.generate(4, worker=1, clock=clock_at())
    assert len(values) == 4
    assert layout.decode(values[0]).worker == 1
