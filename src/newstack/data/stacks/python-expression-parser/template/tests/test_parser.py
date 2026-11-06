import pytest

from {{ package_name }}.nodes import (
    Binary,
    Call,
    Name,
    Number,
    Unary,
)
from {{ package_name }}.parser import (
    ParseError,
    parse,
    precedence_table,
)

CORPUS = [
    "1",
    "1 + 2",
    "1 + 2 * 3",
    "(1 + 2) * 3",
    "2 ^ 3 ^ 2",
    "(2 ^ 3) ^ 2",
    "-2 ^ 2",
    "(-2) ^ 2",
    "1 - 2 - 3",
    "1 - (2 - 3)",
    "max(1, 2, 3)",
    "1 / (2 * (3 + 4))",
    "-(1 + 2) * 3",
    "1 < 2",
    "0.5 * x",
]


def test_a_number_is_a_leaf():
    tree = parse("42")
    assert tree == Number(42)


def test_multiplication_nests_under_addition():
    tree = parse("2 + 3 * 4")
    assert isinstance(tree, Binary) and tree.op == "+"
    assert isinstance(tree.right, Binary) and tree.right.op == "*"


def test_parentheses_change_the_tree():
    assert parse("(2 + 3) * 4") != parse("2 + 3 * 4")


def test_power_is_right_associative():
    tree = parse("2 ^ 3 ^ 2")
    assert isinstance(tree.right, Binary)
    assert tree.left == Number(2)


def test_power_binds_tighter_than_unary_minus():
    tree = parse("-2 ^ 2")
    assert isinstance(tree, Unary) and tree.op == "-"
    assert isinstance(tree.operand, Binary) and tree.operand.op == "^"


def test_a_negative_exponent_is_allowed():
    tree = parse("2 ^ -1")
    assert isinstance(tree.right, Unary)


def test_a_call_takes_several_arguments():
    tree = parse("max(1, 2, 3)")
    assert isinstance(tree, Call)
    assert tree.name == "max"
    assert len(tree.args) == 3


def test_a_name_is_not_a_call():
    assert isinstance(parse("x"), Name)


@pytest.mark.parametrize("source", CORPUS)
def test_render_round_trips(source):
    tree = parse(source)
    assert parse(tree.render()) == tree


def test_a_redundant_parenthesis_is_dropped():
    assert parse("(2 * 3) + 4").render() == "2 * 3 + 4"


def test_a_needed_parenthesis_is_kept():
    assert parse("2 * (3 + 4)").render() == "2 * (3 + 4)"


def test_the_right_side_of_a_minus_keeps_its_group():
    assert parse("1 - (2 - 3)").render() == "1 - (2 - 3)"


def test_the_left_side_of_a_power_keeps_its_group():
    assert parse("(2 ^ 3) ^ 2").render() == "(2 ^ 3) ^ 2"


@pytest.mark.parametrize(
    "source",
    ["2 + * 3", "1 + (2", "1 < 2 < 3", "abs()", "1 + 2 3", "", "max(1,)", "2 $ 3"],
)
def test_broken_input_names_a_column(source):
    with pytest.raises((ParseError, ValueError)) as caught:
        parse(source)
    assert "column" in str(caught.value)


def test_an_unclosed_group_names_where_it_opened():
    with pytest.raises(ParseError) as caught:
        parse("1 + (2")
    assert "opened at column 5" in str(caught.value)


def test_a_chained_comparison_is_refused():
    with pytest.raises(ParseError) as caught:
        parse("1 < 2 < 3")
    assert "chain" in str(caught.value)


def test_the_caret_points_at_the_column():
    with pytest.raises(ParseError) as caught:
        parse("2 + * 3")
    lines = caught.value.caret().splitlines()
    assert lines[0] == "  2 + * 3"
    assert lines[1].index("^") == 6


def test_the_precedence_table_is_ordered():
    rows = precedence_table()
    levels = [level for _, level in rows]
    assert levels == sorted(levels)
