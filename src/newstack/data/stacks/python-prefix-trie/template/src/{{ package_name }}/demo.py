"""Six stories about letters, stems, and what a trie owes its corpus.

Every number printed here is computed at run time by the real modules;
a story that stops holding fails the selftest, not the reader.
"""

from __future__ import annotations

from dataclasses import dataclass

from .corpus import synthetic
from .scan import scan_has, scan_lcp, scan_prefix
from .trie import PrefixTrie
from .workload import run_storm


@dataclass(frozen=True)
class Story:
    """One claim, the numbers behind it, and whether it held."""

    title: str
    detail: str
    held: bool


def stories() -> list[Story]:
    """The six claims the trie makes, each computed fresh."""
    corpus = synthetic(200, seed=9)
    trie = PrefixTrie(corpus)

    probes = [*corpus[::17], "zzzz", "q"]
    answered = all(trie.has(word) is scan_has(corpus, word) for word in probes)
    first = Story(
        "membership answers what a set answers",
        f"{len(probes)} probes, set-equal={answered}, size={trie.count()}",
        answered and trie.count() == len(set(corpus)),
    )

    stems = ["", "a", "co", "zz", "cart"]
    listed = all(trie.prefix(stem) == scan_prefix(corpus, stem) for stem in stems)
    second = Story(
        "every prefix listing equals the sorted scan",
        f"{len(stems)} stems checked, scan-equal={listed}",
        listed,
    )

    whole = trie.prefix("")
    third = Story(
        "the empty prefix lists every word exactly once",
        f"{len(whole)} words listed, once each={whole == sorted(set(corpus))}",
        whole == sorted(set(corpus)),
    )

    victim = corpus[3]
    stem = victim[:2]
    before = trie.prefix(stem)
    trie.delete(victim)
    after = trie.prefix(stem)
    fourth = Story(
        "delete drops the word, survivors keep their stems",
        f"dropped {victim!r}, survivors intact={after == [w for w in before if w != victim]}",
        not trie.has(victim)
        and after == [word for word in before if word != victim],
    )

    shared = scan_lcp(["cart", "car", "cartwheel"])
    fifth = Story(
        "the common prefix belongs to every word it names",
        f"cart/car/cartwheel share {shared!r}, trie agrees="
        f"{PrefixTrie(['cart', 'car', 'cartwheel']).longest_common_prefix() == shared}",
        shared == "car"
        and PrefixTrie(["cart", "car", "cartwheel"]).longest_common_prefix() == shared,
    )

    storm = run_storm(seed=31)
    sixth = Story(
        "a storm keeps every promise after every op",
        f"{storm.steps} steps, {storm.breaks} breaks, seated={storm.ordered}",
        storm.clean,
    )

    return [first, second, third, fourth, fifth, sixth]
