from __future__ import annotations

import pytest

from {{ package_name }}.expr import (
    ExprError,
    Number,
    Op,
)
from {{ package_name }}.yard import (
    balanced,
    postfix_text,
    to_postfix,
)

QUEUES = {
    "1 + 2": "1 2 +",
    "2 + 3 * 4": "2 3 4 * +",
    "( 2 + 3 ) * 4": "2 3 + 4 *",
    "3 + 4 * 2 / ( 1 - 5 ) * 2": "3 4 2 * 1 5 - / 2 * +",
    "100 - 20 - 5": "100 20 - 5 -",
    "7": "7",
}


def test_the_yields_queue_is_the_documented_one() -> None:
    for expr, queue in QUEUES.items():
        assert postfix_text(to_postfix(expr)) == queue


def test_a_queued_operator_pops_what_it_ties() -> None:
    assert postfix_text(to_postfix("2 * 3 + 4")) == "2 3 * 4 +"


def test_a_looser_operator_waits_behind() -> None:
    assert postfix_text(to_postfix("2 + 3 * 4")) == "2 3 4 * +"


def test_parentheses_freeze_the_queue() -> None:
    assert postfix_text(to_postfix("( 1 + 2 ) * 3")) == "1 2 + 3 *"


def test_the_yield_is_balanced_without_parentheses() -> None:
    for expr in QUEUES:
        queue = to_postfix(expr)
        assert balanced(queue)
        assert all(not isinstance(token, str) for token in queue)


def test_an_infix_list_is_not_balanced() -> None:
    assert not balanced(["1", "(", "2"])
    assert not balanced(["1", ")"])


@pytest.mark.parametrize("noise", ["( 1 + 2", "1 + 2 )", ") 1 (", "1 +", "* 3", "1 2"])
def test_a_malformed_expression_is_refused(noise: str) -> None:
    with pytest.raises(ExprError):
        to_postfix(noise)


def test_tokens_are_the_shipped_types() -> None:
    queue = to_postfix("1 + 2")
    assert isinstance(queue[0], Number)
    assert isinstance(queue[-1], Op)
