import pytest

from {{ package_name }} import engine as subject
from {{ package_name }} import events as events_mod

SECOND = events_mod.US
BASE = 1_767_225_600 * SECOND
Aggregation = subject.Aggregation
Engine = subject.Engine
Event = events_mod.Event


def at(minutes: float = 0.0, seconds: float = 0.0) -> int:
    return BASE + int((minutes * 60 + seconds) * SECOND)


def run(values, *, width=60, hop=None, lateness=0, aggregation=Aggregation.COUNT):
    engine = Engine(
        width * SECOND,
        hop_us=None if hop is None else hop * SECOND,
        lateness_us=lateness * SECOND,
        aggregation=aggregation,
    )
    for moment, value in values:
        engine.push(Event(moment, value))
    engine.flush()
    return engine.report()


def test_count_counts_events() -> None:
    report = run([(at(seconds=1), 2.0), (at(seconds=2), 3.0)])
    assert report.windows[0].count == 2


def test_sum_ignores_nulls() -> None:
    report = run([(at(seconds=1), 2.0), (at(seconds=2), None)])
    assert report.windows[0].total == 2
    assert report.windows[0].count == 2


def test_the_mean_of_no_numbers_is_undefined() -> None:
    report = run([(at(seconds=1), None)], aggregation=Aggregation.MEAN)
    assert report.windows[0].mean is None
    assert report.windows[0].value(Aggregation.MEAN) == "-"


def test_late_inside_the_allowance_still_counts() -> None:
    engine = Engine(60 * SECOND, lateness_us=30 * SECOND)
    engine.push(Event(at(seconds=10), 1.0))
    engine.push(Event(at(minutes=1, seconds=20), 1.0))
    engine.push(Event(at(seconds=40), 1.0))  # 20s after the minute ended, still allowed
    assert engine.report().late == []
    engine.push(Event(at(minutes=2), 1.0))  # the watermark reaches 00:01:30
    first = next(item for item in engine.report().windows if item.window.start_us == at())
    assert first.count == 2


def test_past_the_watermark_is_late_and_changes_nothing() -> None:
    engine = Engine(60 * SECOND, lateness_us=30 * SECOND)
    engine.push(Event(at(seconds=10), 1.0))
    engine.push(Event(at(minutes=3, seconds=30), 1.0))
    before = next(item for item in engine.report().windows if item.window.start_us == at())
    engine.push(Event(at(seconds=20), 1.0))
    after = next(item for item in engine.report().windows if item.window.start_us == at())
    assert before.count == after.count == 1
    assert len(engine.report().late) == 1


def test_a_late_report_names_the_window_and_the_watermark() -> None:
    engine = Engine(60 * SECOND, lateness_us=30 * SECOND)
    engine.push(Event(at(seconds=10), 1.0))
    engine.push(Event(at(minutes=3), 1.0))
    engine.push(Event(at(seconds=20), 1.0))
    late = engine.report().late[0]
    assert late.window.start_us == at()
    assert late.watermark_us == at(minutes=3) - 30 * SECOND


def test_a_flushed_window_is_not_final() -> None:
    report = run([(at(seconds=1), 1.0)])
    assert report.windows[0].final is False


def test_windows_without_events_are_missing_not_zero() -> None:
    report = run([(at(seconds=5), 1.0), (at(minutes=2, seconds=5), 1.0)])
    assert len(report.windows) == 2
    assert [window.start_us for window in report.missing()] == [at(minutes=1)]


def test_a_sliding_event_is_counted_twice() -> None:
    report = run([(at(seconds=40), 1.0)], hop=30)
    assert len(report.windows) == 2
    assert sum(item.count for item in report.windows) == 2


def test_the_report_is_json() -> None:
    payload = run([(at(seconds=1), 1.0)]).as_dict()
    assert payload["aggregation"] == "count"
    assert payload["windows"][0]["count"] == 1


def test_an_unknown_aggregation_is_refused() -> None:
    with pytest.raises(subject.EngineError):
        Engine(60 * SECOND, aggregation="median")


def test_a_negative_lateness_is_refused() -> None:
    with pytest.raises(subject.EngineError):
        Engine(60 * SECOND, lateness_us=-1)


def test_a_zero_width_is_refused() -> None:
    with pytest.raises(subject.EngineError):
        Engine(0)


def test_a_hop_wider_than_the_window_is_refused_at_construction() -> None:
    with pytest.raises(subject.EngineError):
        Engine(60 * SECOND, hop_us=120 * SECOND)
