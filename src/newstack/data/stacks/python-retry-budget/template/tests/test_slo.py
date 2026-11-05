from decimal import Decimal

import pytest

from {{ package_name }} import slo as subject


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("99.9", 999000),
        ("99.9%", 999000),
        ("99", 990000),
        ("99.99", 999900),
        ("99.999", 999990),
        ("100", 1000000),
        ("50.5", 505000),
        ("0.001", 10),
    ],
)
def test_a_target_becomes_parts_per_million(text, want):
    assert subject.parse_target(text) == want


@pytest.mark.parametrize("text", ["0", "0.0", "100.1", "101", "-1", "abc", "", "1e3", "99.9999999"])
def test_a_target_that_is_not_a_percentage(text):
    with pytest.raises(subject.SloError):
        subject.parse_target(text)


@pytest.mark.parametrize(
    ("text", "want"),
    [("90s", 90), ("30m", 1800), ("6h", 21600), ("30d", 2592000), ("4w", 2419200)],
)
def test_a_duration_becomes_seconds(text, want):
    assert subject.parse_duration(text) == want


@pytest.mark.parametrize("text", ["0s", "30", "1y", "1.5h", "", "d", "-5m", "1 m"])
def test_a_duration_that_is_not_a_duration(text):
    with pytest.raises(subject.SloError):
        subject.parse_duration(text)


def test_the_budget_is_the_complement_of_the_target():
    slo = subject.slo_of("99.9", "30d")
    assert slo.allowed_ppm == 1000
    assert slo.allowed_fraction == Decimal("0.001")
    assert slo.allowed_bad(1000000) == Decimal("1000.000")


def test_a_perfect_target_has_no_budget_at_all():
    slo = subject.slo_of("100", "1h")
    assert slo.allowed_ppm == 0
    assert slo.allowed_bad(10) == 0


def test_the_target_reads_back_the_way_it_was_written():
    assert subject.slo_of("99.9", "1d").target_text == "99.9%"
    assert subject.slo_of("100", "1d").target_text == "100%"
    assert subject.slo_of("99.99", "1d").target_text == "99.99%"


def test_a_window_of_zero_is_refused():
    with pytest.raises(subject.SloError, match="at least 1 second"):
        subject.slo_of("99.9", 0)
