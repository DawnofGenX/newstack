from __future__ import annotations

import pytest

from {{ package_name }}.rules import (
    DEFAULT_ALPHA,
    RuleError,
    checked_alpha,
    depth_bound,
    heavy_child,
    lower_child,
    violates,
    worst_case_rebuild,
)


def test_the_default_rule_is_seven_tenths() -> None:
    assert DEFAULT_ALPHA == 0.7


def test_a_parent_of_ninety_tolerates_sixty_two() -> None:
    assert heavy_child(0.7, 90) == 62
    assert violates(0.7, 62, 90) is False
    assert violates(0.7, 63, 90) is True


def test_a_rebuild_lands_a_ninety_parent_on_twenty_seven() -> None:
    assert lower_child(0.7, 90) == 27
    for size in range(2, 200):
        assert lower_child(0.7, size) <= heavy_child(0.7, size)


def test_the_worst_bill_is_the_heaviest_tolerated_child() -> None:
    assert worst_case_rebuild(0.7, 90) == heavy_child(0.7, 90)


def test_the_depth_promise_counts_the_log() -> None:
    assert depth_bound(0.7, 45) == 12
    assert depth_bound(0.7, 90) == 14


@pytest.mark.parametrize("alpha", [0.0, 1.0, -0.5, 1.5, True, "x"])
def test_alpha_outside_the_open_interval_keeps_no_rule(alpha: object) -> None:
    with pytest.raises(RuleError):
        checked_alpha(alpha)  # type: ignore[arg-type]


@pytest.mark.parametrize("keys", [0, -3, True, "nine"])
def test_no_keys_stand_no_promise(keys: object) -> None:
    with pytest.raises(RuleError):
        depth_bound(0.7, keys)  # type: ignore[arg-type]
