from decimal import Decimal

import pytest

from {{ package_name }} import buckets as readings
from {{ package_name }} import burn as subject
from {{ package_name }} import slo as slo_module

START = 1_772_000_000 - (1_772_000_000 % 60)


def stream(count, good=1000, bad=0, start=START):
    return [readings.Bucket(start + index * 60, good, bad) for index in range(count)]


@pytest.mark.parametrize(
    ("good", "bad", "want"),
    [
        (0, 0, None),
        (999000, 1000, Decimal(1)),
        (998000, 2000, Decimal(2)),
        (0, 1000, Decimal(1000)),
    ],
)
def test_burn_rate_is_a_ratio_of_ratios(good, bad, want):
    assert subject.burn_rate(good, bad, 1000) == want


def test_a_perfect_target_has_no_burn_rate():
    assert subject.burn_rate(0, 0, 0) is None


def test_a_confirmation_window_cannot_outlive_its_evidence():
    with pytest.raises(subject.BudgetError, match="cannot confirm anything"):
        subject.Rule(300, 600, Decimal(6))


def test_a_threshold_of_zero_is_refused():
    with pytest.raises(subject.BudgetError, match="must be positive"):
        subject.Rule(3600, 300, Decimal(0))


def test_the_three_default_rules_are_the_ones_the_sre_workbook_describes():
    shapes = [(rule.long_s, rule.short_s, rule.threshold) for rule in subject.DEFAULT_POLICY]
    assert shapes == [
        (3600, 300, Decimal("14.4")),
        (21600, 1800, Decimal("6")),
        (259200, 21600, Decimal("1")),
    ]


def test_a_quiet_hour_does_not_page():
    verdict = subject.judge(subject.Rule(3600, 300, Decimal(6)), 10000, 0, 1000, 0, 1000)
    assert verdict.firing is False
    assert verdict.reason == "under the threshold"


def test_an_empty_window_cannot_page():
    verdict = subject.judge(subject.Rule(3600, 300, Decimal(6)), 0, 0, 0, 0, 1000)
    assert verdict.long_burn is None
    assert verdict.firing is False
    assert "no traffic" in verdict.reason


def test_both_windows_over_the_line_pages():
    verdict = subject.judge(subject.Rule(3600, 300, Decimal(6)), 1000, 100, 100, 10, 1000)
    assert verdict.firing is True
    assert "this is happening now" in verdict.reason


def test_a_long_window_over_and_a_short_one_quiet_does_not_page():
    verdict = subject.judge(subject.Rule(3600, 300, Decimal(6)), 1000, 100, 1000, 0, 1000)
    assert verdict.firing is False
    assert "already be over" in verdict.reason


def test_a_long_window_over_with_a_silent_short_one_does_not_page():
    verdict = subject.judge(subject.Rule(3600, 300, Decimal(6)), 1000, 100, 0, 0, 1000)
    assert verdict.firing is False
    assert verdict.short_burn is None


def test_the_budget_is_the_target_applied_to_the_traffic():
    report = subject.report(stream(60), slo_module.slo_of("99.9", "1h"))
    assert report.total == 60000
    assert report.allowed_bad == Decimal("60")
    assert report.remaining == Decimal("60")
    assert report.burn == 0
    assert report.firing is False


def test_spending_the_whole_budget_is_exhaustion():
    report = subject.report(stream(60, good=999, bad=1), slo_module.slo_of("99.9", "1h"))
    assert report.exhausted is True
    assert report.remaining <= 0
    assert "already exhausted" in " ".join(report.lines())


def test_time_to_exhaustion_uses_the_observed_rate():
    report = subject.report(stream(60, good=1000, bad=1), slo_module.slo_of("99.9", "1h"))
    # 60 bad events against a budget of 60.06, burning one every 60 seconds.
    assert report.allowed_bad == Decimal("60.060")
    assert report.remaining.quantize(Decimal("0.001")) == Decimal("0.060")
    assert report.bad_per_second == Decimal(1) / Decimal(60)
    assert report.seconds_to_exhaustion == 3


def test_the_report_names_a_window_that_starts_before_the_data():
    report = subject.report(stream(10), slo_module.slo_of("99.9", "1h"))
    assert report.missing
    assert "silence is not success" in " ".join(report.lines())


def test_a_hole_in_the_middle_is_reported():
    rows = stream(5) + stream(5, start=START + 900)
    report = subject.report(rows, slo_module.slo_of("99.9", "20m"))
    assert report.missing == ((START + 300, START + 900),)


def test_a_window_reaching_past_the_data_is_refused():
    with pytest.raises(subject.BudgetError, match="after the last bucket"):
        subject.report(stream(10), slo_module.slo_of("99.9", "1h"), now_s=START + 3600)


def test_a_window_with_no_traffic_in_it_is_refused():
    with pytest.raises(subject.BudgetError, match="no buckets fall inside"):
        subject.report(stream(10), slo_module.slo_of("99.9", "1h"), now_s=START - 3600)


def test_no_buckets_at_all_is_refused():
    with pytest.raises(subject.BudgetError, match="no buckets"):
        subject.report([], slo_module.slo_of("99.9", "1h"))


def test_the_json_shape_carries_the_numbers_as_strings():
    report = subject.report(stream(5, good=999, bad=1), slo_module.slo_of("99.9", "5m"))
    payload = report.as_dict()
    assert payload["bad"] == 5
    assert payload["budget"]["allowed"] == "5.000"
    assert payload["burn"] == "1"
    assert payload["firing"] is False
