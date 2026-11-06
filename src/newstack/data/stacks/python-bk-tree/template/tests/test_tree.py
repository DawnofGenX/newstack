from __future__ import annotations

from itertools import product

import pytest

from {{ package_name }}.corpus import synthetic
from {{ package_name }}.distance import osa
from {{ package_name }}.tree import BKTree, TreeError, search_by

WORDS = synthetic(300, seed=23)


def tree() -> BKTree:
    return BKTree(WORDS)


def test_a_search_answers_what_a_scan_answers() -> None:
    found = tree()
    for query, radius in [(found.words[3], 1), (found.words[150], 2), ("vquplu", 2)]:
        assert found.search(query, radius).words == found.scan(query, radius).words


def test_the_pruned_walk_looks_at_less_than_it_has() -> None:
    found = tree()
    pruned = found.search(found.words[3], 1)
    assert pruned.visited < len(found)
    assert pruned.compared == pruned.visited
    assert pruned.pruned == len(found) - pruned.visited


def test_a_radius_below_zero_is_refused() -> None:
    with pytest.raises(TreeError):
        tree().search("a", -1)


def test_a_nearest_walk_finds_a_corpus_word_at_zero() -> None:
    found = tree()
    nearest = found.nearest(found.words[12])
    assert nearest.best == 0
    assert nearest.visited < len(found)


def test_an_empty_tree_answers_with_nothing() -> None:
    empty = BKTree()
    assert len(empty) == 0
    assert empty.depth == 0
    assert empty.nearest("anything").hits == ()
    assert empty.search("anything", 1).hits == ()


def test_transpositions_scan_and_say_so() -> None:
    found = tree().search_allowing_transpositions(WORDS[4], 2)
    assert found.full_scan
    truth = sorted(word for word in WORDS if osa(WORDS[4], word) <= 2)
    assert sorted(found.words) == truth


def test_a_walk_with_osa_on_this_tree_loses_an_answer() -> None:
    short = sorted(
        "".join(letters)
        for length in (2, 3)
        for letters in product("ab", repeat=length)
    )
    pruned = search_by(BKTree(short), "aab", 1, distance=osa)
    truth = sorted(word for word in short if osa("aab", word) <= 1)
    assert sorted(pruned.words) != truth


def test_the_shape_follows_the_order_of_insertion() -> None:
    forward = BKTree(WORDS)
    backward = BKTree(list(reversed(WORDS)))
    assert len(forward) == len(backward)
    assert forward.search(WORDS[7], 2).words == backward.search(WORDS[7], 2).words


def test_lines_report_what_the_walk_saw() -> None:
    found = tree().search(WORDS[3], 1)
    body = "\n".join(found.lines())
    assert "pruned by the triangle inequality" in body
    assert f"found      {len(found.hits)} word(s)" in body
