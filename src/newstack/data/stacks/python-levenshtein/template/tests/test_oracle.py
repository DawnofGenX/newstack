from __future__ import annotations

import pytest

from {{ package_name }}.distance import SHIPPED, DistanceError, distance
from {{ package_name }}.oracle import ORACLE_LIMIT, oracle_distance


def test_the_walk_agrees_with_the_recursion_on_shipped_words() -> None:
    for left in SHIPPED:
        for right in SHIPPED:
            if len(left) <= ORACLE_LIMIT and len(right) <= ORACLE_LIMIT:
                assert oracle_distance(left, right) == distance(left, right)


def test_the_oracle_edges_answer_like_the_walk() -> None:
    assert oracle_distance("", "") == 0
    assert oracle_distance("cat", "") == 3
    assert oracle_distance("", "cart") == 4
    assert oracle_distance("cart", "cat") == 1


def test_the_oracle_refuses_a_pair_past_the_limit() -> None:
    with pytest.raises(DistanceError, match="letters at most"):
        oracle_distance("a" * (ORACLE_LIMIT + 1), "b")
    with pytest.raises(DistanceError, match="letters at most"):
        oracle_distance("a", "b" * (ORACLE_LIMIT + 1))


def test_the_limit_is_small_enough_to_be_runnable() -> None:
    assert ORACLE_LIMIT <= 8
