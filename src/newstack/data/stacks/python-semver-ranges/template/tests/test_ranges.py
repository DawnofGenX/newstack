"""Ranges: intervals, prerelease gates, and refusals."""

import pytest

from {{ package_name }} import ranges as subject
from {{ package_name }}.version import parse


def test_a_caret_range_keeps_the_first_non_zero_field():
    assert subject.parse_range("^1.2.3").render() == "[1.2.3, 2.0.0)"
    assert subject.parse_range("^0.2.3").render() == "[0.2.3, 0.3.0)"
    assert subject.parse_range("^0.0.3").render() == "[0.0.3, 0.0.4)"


def test_a_partial_caret_pins_only_what_was_written():
    assert subject.parse_range("^0.0").render() == "[0.0.0, 0.1.0)"
    assert subject.parse_range("^0").render() == "[0.0.0, 1.0.0)"


def test_a_tilde_range_keeps_the_minor():
    assert subject.parse_range("~1.4.2").render() == "[1.4.2, 1.5.0)"
    assert subject.parse_range("~1").render() == "[1.0.0, 2.0.0)"


def test_a_partial_version_is_an_interval():
    assert subject.parse_range("1.2").render() == "[1.2.0, 1.3.0)"
    assert subject.parse_range("1").render() == "[1.0.0, 2.0.0)"
    assert subject.parse_range("1.2.x").render() == "[1.2.0, 1.3.0)"


def test_a_comparator_on_a_partial_version_moves_to_the_edge():
    assert subject.parse_range(">1.2").render() == ">=1.3.0"
    assert subject.parse_range("<=1.2").render() == "<1.3.0"
    assert subject.parse_range("<1.2").render() == "<1.2.0"


def test_a_hyphen_range_reads_both_ends():
    assert subject.parse_range("1.2 - 2.3.4").render() == "[1.2.0, 2.3.4]"
    assert subject.parse_range("1.2.3 - 2.3").render() == "[1.2.3, 2.4.0)"


def test_the_or_operator_is_two_intervals():
    chosen = subject.parse_range("~1.4 || ^2.0")
    assert len(chosen.arms) == 2
    assert chosen.allows(parse("1.4.9"))
    assert chosen.allows(parse("2.5.0"))
    assert not chosen.allows(parse("1.9.0"))


def test_a_prerelease_is_opt_in():
    assert not subject.parse_range("^1.2.0").allows(parse("1.3.0-beta"))
    assert subject.parse_range("1.3.0-beta").allows(parse("1.3.0-beta"))
    assert not subject.parse_range("1.3.0-beta").allows(parse("1.3.0-alpha"))


def test_the_prerelease_gate_is_per_core():
    chosen = subject.parse_range(">=1.3.0-beta <2")
    assert chosen.allows(parse("1.3.0-beta.2"))
    assert chosen.allows(parse("1.3.0"))
    assert not chosen.allows(parse("1.4.0-rc.1"))


def test_a_prerelease_inside_a_named_core_is_still_ordered():
    chosen = subject.parse_range(">=1.3.0-beta <2")
    assert not chosen.allows(parse("1.3.0-alpha"))


def test_an_excluded_bound_is_excluded():
    chosen = subject.parse_range(">1.2.3 <2.0.0")
    assert not chosen.allows(parse("1.2.3"))
    assert chosen.allows(parse("1.2.4"))
    assert not chosen.allows(parse("2.0.0"))


def test_an_inclusive_upper_bound_is_included():
    assert subject.parse_range("<=1.2.3").allows(parse("1.2.3"))


def test_a_contradiction_parses_but_allows_nothing():
    chosen = subject.parse_range(">=2.0.0 <1.0.0")
    assert chosen.arms[0].empty
    assert not chosen.allows(parse("1.5.0"))


@pytest.mark.parametrize("text", ["", "   ", "1.2 || ", "1.two", ">", "* - 1.0.0", "1.2.3 - "])
def test_a_range_that_cannot_be_read_is_refused(text):
    with pytest.raises(subject.RangeError):
        subject.parse_range(text)


def test_the_refusal_points_at_the_problem():
    with pytest.raises(subject.RangeError, match="empty arm"):
        subject.parse_range("1.2 || ")
    with pytest.raises(subject.RangeError, match="direction"):
        subject.parse_range(">")


def test_the_match_reports_the_first_arm():
    chosen = subject.parse_range("^1.0 || ^2.0")
    assert chosen.match(parse("2.1.0")) == 2
    assert chosen.match(parse("3.0.0")) is None
