from __future__ import annotations

import pytest

from {{ package_name }} import syntax


def test_literals_concatenate_into_one_node() -> None:
    node = syntax.parse("abc")
    assert isinstance(node, syntax.Concat)
    assert [part.char for part in node.parts] == ["a", "b", "c"]


def test_alternation_is_the_loosest_operator() -> None:
    node = syntax.parse("ab|cd")
    assert isinstance(node, syntax.Alt)
    assert [option.render() for option in node.options] == ["ab", "cd"]


def test_a_repeat_binds_tighter_than_concatenation() -> None:
    node = syntax.parse("ab*")
    assert isinstance(node, syntax.Concat)
    assert isinstance(node.parts[1], syntax.Repeat)


def test_a_group_can_move_a_repeat() -> None:
    node = syntax.parse("(ab)*")
    assert isinstance(node, syntax.Repeat)
    assert node.body.render() == "ab"


@pytest.mark.parametrize("pattern", ["a*", "a+", "a?", "()", ".", "[a-c]", "\\d", "a|b|c"])
def test_rendering_reads_back_as_the_same_tree(pattern: str) -> None:
    node = syntax.parse(pattern)
    assert syntax.parse(node.render()) == node


def test_rendering_drops_parentheses_that_change_nothing() -> None:
    assert syntax.parse("(a)").render() == "a"
    assert syntax.parse("((ab))").render() == "ab"


def test_rendering_keeps_parentheses_that_change_meaning() -> None:
    assert syntax.parse("(a|b)c").render() == "(a|b)c"
    assert syntax.parse("(ab)*").render() == "(ab)*"


def test_a_class_is_sorted_and_merged() -> None:
    node = syntax.parse("[dbca]")
    assert isinstance(node, syntax.Class)
    assert node.char_class.ranges == ((97, 100),)


def test_a_negated_class_still_prints_its_caret() -> None:
    node = syntax.parse("[^a-c]")
    assert node.render() == "[^a-c]"
    assert node.char_class.matches("z")
    assert not node.char_class.matches("b")


def test_the_metacharacters_can_be_escaped() -> None:
    assert syntax.parse("\\.").render() == "\\."
    assert syntax.parse("\\(").render() == "\\("


def test_shorthand_classes_expand_to_real_ranges() -> None:
    digits = syntax.parse("\\d")
    assert isinstance(digits, syntax.Class)
    assert digits.char_class.matches("7")
    assert not digits.char_class.matches("x")


@pytest.mark.parametrize(
    ("pattern", "needle"),
    [
        ("(ab", "never closed"),
        ("[ab", "never closed"),
        ("*a", "needs something to repeat"),
        ("a)", "has no place here"),
        ("[z-a]", "runs backwards"),
        ("a{3}", "counted repetition"),
        ("\\q", "not an escape"),
        ("a\\", "escapes nothing"),
        ("", "empty pattern"),
        ("[]", "never closed"),
    ],
)
def test_a_pattern_that_cannot_be_read_says_why(pattern: str, needle: str) -> None:
    with pytest.raises(syntax.PatternError) as caught:
        syntax.parse(pattern)
    assert needle in str(caught.value)


def test_the_error_position_points_at_the_character() -> None:
    with pytest.raises(syntax.PatternError) as caught:
        syntax.parse("(ab")
    assert caught.value.position == 3
    assert caught.value.caret("(ab").count("^") == 1


def test_the_alphabet_lists_every_mentioned_character() -> None:
    assert syntax.alphabet(syntax.parse("(cat|dog)s?")) == "acdgost"


def test_an_unmentioned_character_is_not_in_the_pattern() -> None:
    assert syntax.unmentioned_char(syntax.parse("abc")) not in "abc"
