from __future__ import annotations

from {{ package_name }}.corpus import synthetic
from {{ package_name }}.scan import scan_has, scan_lcp, scan_prefix


def test_the_scan_walks_the_corpus_once() -> None:
    corpus = ["car", "cart", "dog"]
    assert scan_has(corpus, "cart")
    assert not scan_has(corpus, "carpet")
    assert not scan_has([], "anything")


def test_the_scan_lists_the_sorted_suffix() -> None:
    corpus = synthetic(80, seed=3)
    for stem in ("", "a", "co", "zz"):
        assert scan_prefix(corpus, stem) == sorted(
            word for word in corpus if word.startswith(stem)
        )


def test_the_scan_trims_to_what_is_shared() -> None:
    assert scan_lcp(["cart", "car", "cartwheel"]) == "car"
    assert scan_lcp(["car", "dog"]) == ""
    assert scan_lcp(["solo"]) == "solo"
    assert scan_lcp([]) == ""
