from __future__ import annotations

import pytest

from {{ package_name }}.calc import (
    value_of,
)
from {{ package_name }}.expr import (
    ExprError,
    read_expr,
)
from {{ package_name }}.oracle import (
    descent,
)

EXPRS = (
    "7",
    "1 + 2",
    "2 + 3 * 4",
    "8 - 3 - 2",
    "20 / 4 / 2",
    "( 1 + 2 ) * 3",
    "3 + 4 * 2 / ( 1 - 5 ) * 2",
    "7 / 2",
    "0 + 12",
    "2 * ( 3 + 4 ) - 5",
    "100 - ( 20 - 5 )",
    "9 / 2 / 2",
    "1 + 2 * 3 - 4 / 2",
)


@pytest.mark.parametrize("expr", EXPRS)
def test_the_oracle_answers_value_of(expr: str) -> None:
    assert descent(expr) == value_of(expr)


def test_the_oracle_eats_a_token_list_too() -> None:
    assert descent(read_expr("6 / 4")) == 1


def test_the_oracle_refuses_the_same_edges() -> None:
    for noise in ("5 / 0", "( 1 + 2", "1 +", "1 2"):
        with pytest.raises(ExprError):
            descent(noise)


def test_the_oracle_descends_where_the_yards_park() -> None:
    assert descent("2 + 3 * 4") == 14
    assert descent("2 * 3 + 4") == 10
