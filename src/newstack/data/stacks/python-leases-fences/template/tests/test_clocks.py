from {{ package_name }} import clocks as subject


def test_a_clock_starts_where_it_was_set() -> None:
    assert subject.ManualClock(250).now_ms() == 250


def test_advancing_returns_the_new_time() -> None:
    clock = subject.ManualClock()
    assert clock.advance(40) == 40
    assert clock.now_ms() == 40


def test_a_clock_cannot_start_negative() -> None:
    try:
        subject.ManualClock(-1)
    except subject.ClockError as error:
        assert "before 0" in str(error)
    else:
        raise AssertionError("a negative start was accepted")


def test_time_does_not_run_backwards() -> None:
    try:
        subject.ManualClock().advance(-1)
    except subject.ClockError as error:
        assert "backwards" in str(error)
    else:
        raise AssertionError("a negative advance was accepted")
