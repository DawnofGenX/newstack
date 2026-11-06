"""The arithmetic, checked against values that do not depend on this module."""

from __future__ import annotations

import pytest

from {{ package_name }} import stats as subject


def test_the_normal_tail_matches_the_textbook() -> None:
    assert subject.normal_cdf(0.0) == pytest.approx(0.5)
    assert subject.normal_cdf(1.959963984540054) == pytest.approx(0.975, abs=1e-9)
    assert subject.two_sided_p(1.959963984540054) == pytest.approx(0.05, abs=1e-6)


def test_the_quantile_inverts_the_tail() -> None:
    for probability in (0.5, 0.9, 0.975, 0.995):
        z = subject.normal_quantile(probability)
        assert subject.normal_cdf(z) == pytest.approx(probability, abs=1e-6)


@pytest.mark.parametrize("probability", [-0.1, 0.0, 1.0, 1.5])
def test_an_impossible_probability_is_refused(probability: float) -> None:
    with pytest.raises(subject.StatsError, match="strictly between 0 and 1"):
        subject.normal_quantile(probability)


def test_an_arm_needs_sensible_numbers() -> None:
    with pytest.raises(subject.StatsError, match="has no visitors"):
        subject.Arm("control", 0, 0)
    with pytest.raises(subject.StatsError, match="which is impossible"):
        subject.Arm("control", 11, 10)
    with pytest.raises(subject.StatsError, match="non-integer"):
        subject.Arm("control", True, 10)


def test_an_arm_parses_from_its_text_form() -> None:
    arm = subject.Arm.from_text("control=130/1000")
    assert (arm.name, arm.conversions, arm.visitors) == ("control", 130, 1000)
    assert arm.rate == pytest.approx(0.13)
    with pytest.raises(subject.StatsError, match="does not hold two whole numbers"):
        subject.Arm.from_text("control=10/x")


def test_wilson_brackets_the_rate_and_holds_its_edges() -> None:
    interval = subject.wilson(50, 100)
    assert interval.low < 0.5 < interval.high
    assert interval.low == pytest.approx(0.4038, abs=1e-4)
    assert interval.high == pytest.approx(0.5962, abs=1e-4)
    assert subject.wilson(0, 10).low == pytest.approx(0.0, abs=1e-12)
    assert subject.wilson(10, 10).high == pytest.approx(1.0, abs=1e-12)
    assert subject.wilson(10, 10).low == pytest.approx(0.7225, abs=1e-4)


def test_the_pooled_error_is_the_unpooled_one_at_equal_rates() -> None:
    same = subject.Arm("control", 40, 500)
    assert subject.pooled_error(same, same) == pytest.approx(subject.standard_error(same, same))
    control = subject.Arm("control", 100, 1000)
    treatment = subject.Arm("treatment", 130, 1000)
    shared = 0.115
    expected = (shared * (1.0 - shared) * (1.0 / 1000 + 1.0 / 1000)) ** 0.5
    assert subject.pooled_error(control, treatment) == pytest.approx(expected)
    assert subject.pooled_error(control, treatment) != subject.standard_error(control, treatment)


def test_a_real_difference_is_significant() -> None:
    result = subject.compare(
        subject.Arm("control", 100, 1000), subject.Arm("treatment", 130, 1000)
    )
    assert result.difference == pytest.approx(0.03)
    assert result.lift == pytest.approx(0.30)
    assert result.z == pytest.approx(2.1027, abs=1e-4)
    assert result.p_value == pytest.approx(0.0355, abs=1e-4)
    assert result.significant()
    assert result.direction() == "higher"
    assert result.interval.contains(0.03)
    assert not result.lift_interval().contains(0.0)


def test_the_same_numbers_twice_are_not_significant() -> None:
    left = subject.Arm("control", 40, 500)
    result = subject.compare(left, subject.Arm("treatment", 40, 500))
    assert result.p_value == 1.0
    assert result.z == 0.0
    assert result.direction() == "indistinguishable"


def test_a_zero_baseline_has_no_finite_lift_interval() -> None:
    result = subject.compare(subject.Arm("control", 0, 200), subject.Arm("treatment", 5, 200))
    assert result.lift == float("inf")
    with pytest.raises(subject.StatsError, match="has no finite interval"):
        result.lift_interval()


def test_the_sample_size_grows_as_the_lift_shrinks() -> None:
    big = subject.sample_per_arm(0.10, 0.20)
    small = subject.sample_per_arm(0.10, 0.05)
    assert big < small
    assert small == 57763


def test_the_detectable_lift_shrinks_with_traffic() -> None:
    wide = subject.detectable_lift(0.10, 20_000)
    narrow = subject.detectable_lift(0.10, 5_000)
    assert wide == pytest.approx(0.0856, abs=1e-3)
    assert narrow > wide


def test_an_impossible_power_request_is_refused() -> None:
    with pytest.raises(subject.StatsError, match="baseline rate is a probability"):
        subject.sample_per_arm(1.5, 0.05)
    with pytest.raises(subject.StatsError, match="infinite sample"):
        subject.sample_per_arm(0.10, 0.0)
    with pytest.raises(subject.StatsError, match="power is a probability"):
        subject.sample_per_arm(0.10, 0.05, power=1.5)


def test_the_comparison_prints_an_interval_beside_each_arm() -> None:
    text = "\n".join(
        subject.compare(
            subject.Arm("control", 100, 1000), subject.Arm("treatment", 130, 1000)
        ).lines()
    )
    assert "wilson" in text
    assert "0.0355" in text
    assert "higher" in text
