"""Reading a stream back: order, duplicates, collisions, spacing."""

import pytest

from {{ package_name }} import audit as subject
from {{ package_name }} import layout


def stream(count=5, worker=1):
    clock = subject_clock()
    generator = subject_generator(worker, clock)
    values = []
    for _ in range(count):
        values.append(generator.next_id())
        clock.advance(1)
    return values


def subject_clock(offset=0):
    from {{ package_name }} import generator

    return generator.ManualClock(layout.EPOCH_MS + offset)


def subject_generator(worker, clock):
    from {{ package_name }} import generator

    return generator.SnowflakeGenerator(worker, clock=clock)


def test_a_clean_stream_is_sound():
    report = subject.audit(stream())
    assert report.held()
    assert report.duplicates == 0
    assert report.workers == (1,)


def test_a_duplicate_is_reported():
    values = stream()
    report = subject.audit([*values, values[-1]])
    assert report.duplicates == 1
    assert not report.monotone


def test_the_span_counts_milliseconds():
    assert subject.audit(stream(5)).span_ms == 4


def test_an_empty_stream_is_refused():
    with pytest.raises(layout.LayoutError, match="empty"):
        subject.audit([])


def test_two_workers_cannot_collide():
    left, right = subject.collision(0, 1, relative_ms=17)
    assert left != right
    assert layout.decode(left).worker == 0
    assert layout.decode(right).worker == 1


def test_spacing_finds_the_smallest_gap():
    assert subject.spacing([5, 6, 9]) == 1


def test_spacing_needs_two_identifiers():
    with pytest.raises(layout.LayoutError, match="two"):
        subject.spacing([5])


def test_the_report_lines_name_the_facts():
    text = "\n".join(subject.audit(stream()).lines())
    assert "identifiers" in text
    assert "distinct" in text
    assert "order" in text
