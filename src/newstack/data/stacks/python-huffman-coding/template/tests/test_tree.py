from __future__ import annotations

from {{ package_name }}.tree import (
    Branch,
    Leaf,
    TreeError,
    build_tree,
    depths,
    height,
    walk,
)


def test_the_ladder_takes_the_two_cheapest_never_the_third() -> None:
    ladder = build_tree({"a": 1, "b": 1, "c": 5})
    assert isinstance(ladder, Branch)
    assert isinstance(ladder.left, Branch)
    assert ladder.left.left == Leaf("a", 1)
    assert ladder.left.right == Leaf("b", 1)
    assert ladder.right == Leaf("c", 5)


def test_ties_fall_alphabetically() -> None:
    ladder = build_tree({"b": 1, "a": 1, "c": 5})
    assert isinstance(ladder.left.left, Leaf)
    assert ladder.left.left.letter == "a"


def test_the_ladder_is_deterministic() -> None:
    weights = {"a": 3, "b": 2, "c": 2, "d": 9}
    assert build_tree(weights) == build_tree(dict(reversed(list(weights.items()))))


def test_the_ladder_weighs_the_whole_text() -> None:
    assert build_tree({"a": 3, "b": 4}).weight == 7


def test_walk_turns_bits_into_letters() -> None:
    ladder = build_tree({"a": 1, "b": 1, "c": 5})
    assert walk(ladder, "00") == "a"
    assert walk(ladder, "1") == "c"


def test_walk_refuses_half_words_and_noise() -> None:
    ladder = build_tree({"a": 1, "b": 1, "c": 5})
    for bits in ("", "2", "000", "11"):
        try:
            walk(ladder, bits)
        except TreeError:
            continue
        raise AssertionError(f"{bits!r} should walk nowhere")


def test_the_harvest_names_every_letter_with_its_road() -> None:
    ladder = build_tree({"a": 1, "b": 1, "c": 5})
    assert depths(ladder) == {"a": 2, "b": 2, "c": 1}
    assert height(ladder) == 2


def test_no_tree_from_no_letters() -> None:
    try:
        build_tree({})
    except TreeError:
        return
    raise AssertionError("an empty map builds no ladder")
