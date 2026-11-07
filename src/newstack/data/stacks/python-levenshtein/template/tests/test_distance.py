from __future__ import annotations

import pytest

from {{ package_name }}.distance import (
    SHIPPED,
    TRIPLES,
    DistanceError,
    distance,
    nearest,
    rank_pairs,
)
from {{ package_name }}.words import WordError


def reference(left: str, right: str) -> int:
    """A second opinion: the full matrix, spelled out."""
    rows = [[0] * (len(right) + 1) for _ in range(len(left) + 1)]
    for i in range(len(left) + 1):
        rows[i][0] = i
    for j in range(len(right) + 1):
        rows[0][j] = j
    for i in range(1, len(left) + 1):
        for j in range(1, len(right) + 1):
            step = 0 if left[i - 1] == right[j - 1] else 1
            rows[i][j] = min(
                rows[i - 1][j] + 1,
                rows[i][j - 1] + 1,
                rows[i - 1][j - 1] + step,
            )
    return rows[len(left)][len(right)]


def test_a_pair_costs_what_the_matrix_costs() -> None:
    for left in ("cat", "cart", "kitten", "sitting", "", "a"):
        for right in ("dog", "do", "kitten", "", "sit"):
            assert distance(left, right) == reference(left, right)


def test_known_distances_are_small_integers() -> None:
    assert distance("cat", "cat") == 0
    assert distance("cart", "cat") == 1
    assert distance("cat", "") == 3
    assert distance("", "cart") == 4
    assert distance("knight", "light") == 2


def test_a_distance_is_the_same_seen_from_either_side() -> None:
    for left in SHIPPED:
        for right in SHIPPED:
            assert distance(left, right) == distance(right, left)


def test_a_detour_never_beats_the_direct_change() -> None:
    for left, middle, right in TRIPLES:
        direct = distance(left, right)
        assert direct <= distance(left, middle) + distance(middle, right)
    for left in SHIPPED:
        for middle in SHIPPED:
            for right in SHIPPED:
                assert distance(left, right) <= (
                    distance(left, middle) + distance(middle, right)
                )


def test_to_the_empty_string_is_a_change_per_letter() -> None:
    for word in SHIPPED:
        assert distance(word, "") == len(word)
        assert distance("", word) == len(word)
    assert distance("", "") == 0


def test_rank_pairs_orders_by_distance_then_letters() -> None:
    ranked = rank_pairs("crt", ["cart", "cat", "dog", "car"])
    assert ranked[0] == (1, "cart")
    assert ranked == sorted(ranked, key=lambda pair: (pair[0], pair[1]))


def test_nearest_is_the_scan_head_and_ties_go_first_by_letters() -> None:
    corpus = ["cart", "cat", "car", "dog"]
    assert nearest("crt", corpus) == "cart"
    assert nearest("cat", corpus) == "cat"
    for query in ("kat", "dot", "zz"):
        head = nearest(query, corpus)
        best = distance(query, head)
        assert all(best <= distance(query, word) for word in corpus)
        tied = sorted(word for word in corpus if distance(query, word) == best)
        assert head == tied[0]


def test_an_empty_corpus_has_no_nearest() -> None:
    with pytest.raises(DistanceError, match="empty corpus"):
        nearest("cat", [])


def test_a_non_string_side_is_refused() -> None:
    for stranger in (7, None, ["cat"]):
        with pytest.raises((DistanceError, WordError)):
            distance(stranger, "cat")
