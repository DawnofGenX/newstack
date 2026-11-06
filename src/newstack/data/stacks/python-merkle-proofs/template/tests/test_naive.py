"""The two wrong trees, measured instead of described."""

from __future__ import annotations

from {{ package_name }} import naive as subject
from {{ package_name }}.hashing import hex_of, leaf_hash
from {{ package_name }}.tree import EMPTY_ROOT, Tree

LEAVES = [f"entry-{number:02d}".encode() for number in range(1, 6)]


def test_without_a_prefix_a_node_passes_as_a_leaf() -> None:
    numbers = subject.forgery(LEAVES)
    assert numbers["two_leaf_bare_root"] == numbers["forged_bare_root"]
    assert numbers["forged_leaf_bytes"] == 64


def test_with_a_prefix_the_same_forgery_fails() -> None:
    numbers = subject.forgery(LEAVES)
    assert numbers["two_leaf_prefixed_root"] != numbers["forged_prefixed_root"]


def test_the_bare_tree_is_a_different_tree() -> None:
    assert hex_of(subject.bare_root(LEAVES)) != hex_of(Tree(LEAVES).root())


def test_duplicating_the_odd_node_changes_the_root() -> None:
    assert subject.duplicate_root(LEAVES) != Tree(LEAVES).root()
    assert hex_of(subject.duplicate_root(LEAVES)) == (
        "f8a8baf16827be866e7fbb3f6c725964ec7e663d4e95cf3dedfd3457b9801f74"
    )


def test_the_duplicate_rule_is_only_visible_on_odd_counts() -> None:
    even = [b"a", b"b", b"c", b"d"]
    assert subject.duplicate_root(even) == Tree(even).root()
    odd = [b"a", b"b", b"c"]
    assert subject.duplicate_root(odd) != Tree(odd).root()


def test_the_degenerate_cases_agree() -> None:
    assert subject.duplicate_root([]) == EMPTY_ROOT
    assert subject.duplicate_root([b"only"]) == leaf_hash(b"only")
    assert subject.bare_root([]) == EMPTY_ROOT
