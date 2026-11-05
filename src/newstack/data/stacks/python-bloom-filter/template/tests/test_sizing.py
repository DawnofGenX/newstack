import math

import pytest

from {{ package_name }} import bloom as subject


def test_the_textbook_sizing_for_one_percent_at_a_thousand() -> None:
    sizing = subject.sized_for(1_000, 0.01)
    assert sizing.m_bits == 9_586
    assert sizing.k_hashes == 7
    assert sizing.bits_per_item == pytest.approx(9.586, abs=0.001)


def test_the_predicted_rate_is_near_the_target() -> None:
    for target in (0.1, 0.01, 0.001):
        sizing = subject.sized_for(2_000, target)
        assert sizing.predicted_rate == pytest.approx(target, rel=0.05)


def test_a_tighter_target_costs_more_bits_and_a_bigger_set_costs_more_bits() -> None:
    loose = subject.sized_for(1_000, 0.1)
    tight = subject.sized_for(1_000, 0.001)
    bigger = subject.sized_for(10_000, 0.1)
    assert tight.m_bits > loose.m_bits
    assert bigger.m_bits > loose.m_bits


def test_the_hash_count_is_the_optimum_not_one_more() -> None:
    sizing = subject.sized_for(1_000, 0.01)
    optimum = sizing.m_bits / sizing.expected * math.log(2)
    assert abs(sizing.k_hashes - optimum) <= 0.5


def test_the_lines_say_what_was_chosen_and_why() -> None:
    text = "\n".join(subject.sized_for(1_000, 0.01).lines())
    assert "bits        9586 (9.59 per item)" in text
    assert "hashes      7" in text
    assert "predicted   0.010035" in text


@pytest.mark.parametrize("expected", [0, -1, True, 1.5, "10"])
def test_a_bad_item_count_is_refused(expected: object) -> None:
    with pytest.raises(subject.BloomFilterError):
        subject.sized_for(expected, 0.01)  # type: ignore[arg-type]


@pytest.mark.parametrize("rate", [0, 1, -0.1, 1.5, "0.1", True])
def test_a_rate_outside_the_open_unit_interval_is_refused(rate: object) -> None:
    with pytest.raises(subject.BloomFilterError):
        subject.sized_for(1_000, rate)  # type: ignore[arg-type]
