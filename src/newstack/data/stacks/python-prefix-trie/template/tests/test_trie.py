from __future__ import annotations

import random

import pytest

from {{ package_name }}.corpus import synthetic
from {{ package_name }}.trie import PrefixTrie
from {{ package_name }}.words import WordError

SEEDS = (7, 23, 91, 1009)


def sample() -> PrefixTrie:
    return PrefixTrie(["car", "cart", "cartwheel", "cat", "catch", "dog", "do"])


def picked(seed: int, corpus: list[str]) -> int:
    return random.Random(seed).randrange(len(corpus))


def test_a_fresh_trie_is_empty_but_answering() -> None:
    empty = PrefixTrie()
    assert empty.walk() == []
    assert empty.prefix("a") == []
    assert empty.count() == 0
    assert len(empty) == 0
    assert empty.invariant()
    assert empty.audit() == []
    assert not empty.has("car")
    assert empty.delete("car") is False
    assert empty.longest_common_prefix() == ""


def test_the_walk_is_the_sorted_corpus() -> None:
    for seed in SEEDS:
        corpus = synthetic(90, seed=seed)
        found = PrefixTrie(corpus)
        assert found.walk() == sorted(set(corpus))
        assert list(found) == sorted(set(corpus))
        assert found.count() == len(set(corpus))


def test_membership_answers_what_a_set_answers() -> None:
    for seed in SEEDS:
        corpus = synthetic(90, seed=seed)
        found = PrefixTrie(corpus)
        stored = set(corpus)
        rng = random.Random(seed * 13)
        for _ in range(50):
            probe = rng.choice([*corpus, "zzzzzz", "q", "a"])
            assert found.has(probe) is (probe in stored)


def test_every_prefix_listing_is_the_sorted_scan() -> None:
    for seed in SEEDS:
        corpus = synthetic(90, seed=seed)
        found = PrefixTrie(corpus)
        stored = sorted(set(corpus))
        stems = ["", "a", "ab", "z", "qu", corpus[3][:2], corpus[4][:3]]
        for stem in stems:
            assert found.prefix(stem) == sorted(
                word for word in stored if word.startswith(stem)
            )


def test_the_empty_prefix_lists_every_word_once() -> None:
    for seed in SEEDS:
        corpus = synthetic(60, seed=seed)
        listed = PrefixTrie(corpus).prefix("")
        assert listed == sorted(set(corpus))
        assert len(listed) == len(set(corpus))
        assert len(set(listed)) == len(listed)


def test_delete_drops_only_the_exact_word() -> None:
    for seed in SEEDS:
        corpus = sorted(set(synthetic(60, seed=seed)))
        found = PrefixTrie(corpus)
        victim = corpus[picked(seed, corpus)]
        stem = victim[:2]
        before = found.prefix(stem)
        assert found.delete(victim) is True
        assert found.delete(victim) is False
        assert not found.has(victim)
        assert found.prefix(stem) == [word for word in before if word != victim]
        assert found.count() == len(corpus) - 1
        assert found.invariant()
        assert found.audit() == []


def test_a_word_survives_its_longer_neighbour() -> None:
    found = sample()
    assert found.delete("cart") is True
    assert found.has("car")
    assert not found.has("cart")
    assert found.has("cartwheel")
    assert found.prefix("car") == ["car", "cartwheel"]
    assert found.delete("car") is True
    assert found.prefix("car") == ["cartwheel"]


def test_insert_lands_once_and_the_gate_refuses_strangers() -> None:
    found = PrefixTrie()
    assert found.insert("kitten") is True
    assert found.insert("kitten") is False
    assert found.count() == 1
    with pytest.raises(WordError):
        found.insert("Kitten")
    with pytest.raises(WordError):
        found.has("")
    with pytest.raises(WordError):
        found.prefix("Cat")


def test_the_common_stem_belongs_to_every_word() -> None:
    assert PrefixTrie(["cart", "car", "cartwheel"]).longest_common_prefix() == "car"
    assert PrefixTrie(["car", "dog"]).longest_common_prefix() == ""
    assert PrefixTrie(["solo"]).longest_common_prefix() == "solo"
    corpus = synthetic(40, seed=11)
    shared = PrefixTrie(corpus).longest_common_prefix()
    assert all(word.startswith(shared) for word in corpus)


def test_a_rebuild_reproduces_every_answer() -> None:
    corpus = synthetic(70, seed=19)
    forward = PrefixTrie(corpus)
    back = PrefixTrie(list(reversed(corpus)))
    mixed = PrefixTrie(list(random.Random(5).sample(corpus, len(corpus))))
    assert forward.walk() == back.walk() == mixed.walk()
    for stem in ("", "a", corpus[0][:2]):
        assert forward.prefix(stem) == back.prefix(stem) == mixed.prefix(stem)
