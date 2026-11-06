"""The gate that runs before anybody forms an opinion about the lift."""

from __future__ import annotations

import pytest

from {{ package_name }} import srm as subject
from {{ package_name }}.stats import Arm


def test_a_perfect_split_is_plausible() -> None:
    result = subject.check(Arm("control", 500, 5_000), Arm("treatment", 500, 5_000))
    assert result.ratio == pytest.approx(0.5)
    assert result.chi_square == pytest.approx(0.0)
    assert result.p_value == pytest.approx(1.0)
    assert not result.mismatched


def test_a_one_percent_imbalance_is_obvious() -> None:
    result = subject.check(Arm("control", 500, 102_000), Arm("treatment", 500, 100_000))
    assert result.ratio == pytest.approx(0.5050, abs=1e-4)
    assert result.chi_square == pytest.approx(19.802, abs=1e-3)
    assert result.p_value == pytest.approx(8.589e-06, rel=1e-3)
    assert result.mismatched


def test_a_small_imbalance_is_within_noise() -> None:
    result = subject.check(Arm("control", 500, 50_100), Arm("treatment", 500, 50_000))
    assert not result.mismatched


def test_the_alpha_is_the_line_the_gate_uses() -> None:
    control, treatment = Arm("control", 500, 50_100), Arm("treatment", 500, 50_000)
    assert subject.check(control, treatment, alpha=0.001).mismatched is False
    assert subject.check(control, treatment, alpha=0.9).mismatched is True


def test_the_expected_split_can_be_lopsided() -> None:
    result = subject.check(Arm("control", 100, 10_000), Arm("treatment", 400, 30_000), split=0.25)
    assert not result.mismatched
    assert result.expected == pytest.approx(0.25)


def test_an_impossible_split_is_refused() -> None:
    with pytest.raises(subject.StatsError, match="a split is a probability"):
        subject.check(Arm("control", 1, 10), Arm("treatment", 1, 10), split=1.0)


def test_the_chi_square_needs_matching_cells() -> None:
    with pytest.raises(subject.StatsError, match="same number of cells"):
        subject.chi_square((1, 2), (0.5,))
    with pytest.raises(subject.StatsError, match="positive"):
        subject.chi_square((1, 2), (0.5, 0.0))


def test_the_lines_name_the_verdict() -> None:
    text = "\n".join(
        subject.check(Arm("control", 500, 102_000), Arm("treatment", 500, 100_000)).lines()
    )
    assert "MISMATCH" in text
    assert "split" in text
