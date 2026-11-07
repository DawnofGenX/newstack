from __future__ import annotations

import itertools
import random

import pytest

from {{ package_name }}.corpus import synthetic
from {{ package_name }}.suffix import SuffixArray, SuffixError, build
from {{ package_name }}.text import TextError

SEEDS = (7, 23, 91, 1009)
TEXTS = ("banana", "mississippi", "abracadabra", "aaaa", "abcabcabc", "a")


def pair_lcp(text: str, left: int, right: int) -> int:
    """Letters two suffixes share, counted the plain way."""
    if left == right:
        return len(text) - left
    stop = 0
    while stop < min(len(text) - left, len(text) - right):
        if text[left + stop] != text[right + stop]:
            break
        stop += 1
    return stop


def census(text: str, pattern: str) -> int:
    """Starts where the pattern begins, overlaps included."""
    return sum(1 for at in range(len(text)) if text.startswith(pattern, at))


def test_the_array_is_the_plain_slice_sort() -> None:
    for text in TEXTS:
        assert SuffixArray(text).array == sorted(
            range(len(text)), key=lambda at: text[at:]
        )
    for seed in SEEDS:
        for text in synthetic(12, seed=seed):
            assert SuffixArray(text).array == sorted(
                range(len(text)), key=lambda at: text[at:]
            )


def test_the_count_is_every_start_overlaps_honest() -> None:
    table = SuffixArray("aaaa")
    assert table.count("a") == 4
    assert table.count("aa") == 3
    assert table.count("aaa") == 2
    assert table.count("aaaa") == 1
    assert table.positions("aa") == [2, 1, 0]
    assert table.count("z") == 0
    for text in ("banana", "mississippi"):
        built = SuffixArray(text)
        for size in (1, 2, 3):
            for start in range(len(text) - size + 1):
                pattern = text[start : start + size]
                assert built.count(pattern) == census(text, pattern)


def test_the_array_orders_and_the_table_is_seated() -> None:
    for text in TEXTS:
        table = SuffixArray(text)
        order = table.array
        assert all(
            text[a:] <= text[b:] for a, b in itertools.pairwise(order)
        )
        assert table.invariant()
        assert table.audit() == []


def test_two_suffixes_share_what_letters_agree() -> None:
    for text in ("banana", "mississippi"):
        table = SuffixArray(text)
        rng = random.Random(11)
        for _ in range(10):
            left = rng.randrange(len(text))
            right = rng.randrange(len(text))
            assert table.lcp(left, right) == pair_lcp(text, left, right)
        assert table.lcp(0, 0) == len(text)


def test_the_lcp_array_pairs_the_neighbours() -> None:
    for text in ("banana", "mississippi", "aaaa"):
        table = SuffixArray(text)
        order = sorted(range(len(text)), key=lambda at: text[at:])
        assert table.lcp_array() == [
            pair_lcp(text, order[k], order[k + 1]) for k in range(len(order) - 1)
        ]


def test_the_longest_repeat_is_the_tallest_share() -> None:
    for text in TEXTS:
        table = SuffixArray(text)
        order = sorted(range(len(text)), key=lambda at: text[at:])
        shares = [
            pair_lcp(text, order[k], order[k + 1]) for k in range(len(order) - 1)
        ]
        tallest = max(shares, default=0)
        expected = (
            "" if tallest == 0 else text[order[shares.index(tallest)] :][:tallest]
        )
        assert table.longest_repeat() == expected


def test_a_place_past_the_text_is_named() -> None:
    table = SuffixArray("banana")
    with pytest.raises(SuffixError):
        table.suffix_at(99)
    with pytest.raises(SuffixError):
        table.lcp(0, 99)


def test_build_blesses_the_text_and_empty_is_seated() -> None:
    assert build("banana").text == "banana"
    with pytest.raises(TextError):
        build("Banana")
    bare = build("")
    assert bare.array == []
    assert bare.invariant()
    assert len(bare) == 0
