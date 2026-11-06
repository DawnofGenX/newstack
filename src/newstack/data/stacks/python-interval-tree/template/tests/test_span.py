from __future__ import annotations

import pytest

from {{ package_name }}.span import Interval, SpanError


def test_a_span_names_every_point_but_its_end() -> None:
    span = Interval(1, 4)
    assert span.holds(1) is True
    assert span.holds(3) is True
    assert span.holds(4) is False
    assert span.holds(0) is False


def test_touching_spans_do_not_overlap() -> None:
    left, right = Interval(1, 3), Interval(3, 5)
    assert left.overlaps(right) is False
    assert right.overlaps(left) is False
    assert Interval(1, 4).overlaps(right) is True


def test_display_states_the_half_open_shape() -> None:
    assert Interval(-2, 7).display() == "[-2..7)"


def test_sorting_is_by_start_then_end() -> None:
    spans = sorted([Interval(3, 9), Interval(1, 8), Interval(1, 4)])
    assert spans == [Interval(1, 4), Interval(1, 8), Interval(3, 9)]


def test_an_empty_or_inverted_span_is_refused() -> None:
    with pytest.raises(SpanError):
        Interval(4, 4)
    with pytest.raises(SpanError):
        Interval(9, 2)


def test_a_span_of_everyday_type_names_itself() -> None:
    with pytest.raises(SpanError):
        Interval("one", 4)  # type: ignore[arg-type]
    with pytest.raises(SpanError):
        Interval(1, 4.5)  # type: ignore[arg-type]
