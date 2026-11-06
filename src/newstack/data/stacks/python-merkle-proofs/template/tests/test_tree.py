"""The tree's shape, and the proofs that depend on it."""

from __future__ import annotations

import pytest

from {{ package_name }} import tree as subject
from {{ package_name }}.hashing import hex_of, leaf_hash

LEAVES = [f"entry-{number:02d}".encode() for number in range(1, 6)]
ROOT_FIVE = "d8fdb1f0c326081f8917ea62b5551153f7f2ad06edf53202861eb36afe8f360d"


def test_the_split_is_the_largest_power_of_two_below_the_count() -> None:
    measured = {count: subject.split_point(count) for count in range(2, 18)}
    assert measured == {
        2: 1, 3: 2, 4: 2, 5: 4, 6: 4, 7: 4, 8: 4,
        9: 8, 10: 8, 11: 8, 12: 8, 13: 8, 14: 8, 15: 8, 16: 8, 17: 16,
    }


def test_one_leaf_cannot_be_split() -> None:
    with pytest.raises(subject.TreeError, match="cannot be split"):
        subject.split_point(1)


def test_depth_is_the_upper_bound_of_the_sibling_count() -> None:
    assert [subject.depth(size) for size in (1, 2, 3, 4, 5, 8, 9, 17)] == [
        0, 1, 2, 2, 3, 3, 4, 5,
    ]


def test_the_rfc_shape_is_not_level() -> None:
    measured = {
        size: [subject.siblings_needed(index, size) for index in range(size)]
        for size in range(2, 10)
    }
    assert measured == {
        2: [1, 1],
        3: [2, 2, 1],
        4: [2, 2, 2, 2],
        5: [3, 3, 3, 3, 1],
        6: [3, 3, 3, 3, 2, 2],
        7: [3, 3, 3, 3, 3, 3, 2],
        8: [3, 3, 3, 3, 3, 3, 3, 3],
        9: [4, 4, 4, 4, 4, 4, 4, 4, 1],
    }
    for size in range(1, 18):
        for index in range(size):
            assert subject.siblings_needed(index, size) <= subject.depth(size)


def test_the_empty_tree_has_the_empty_root() -> None:
    assert subject.Tree([]).root() == subject.EMPTY_ROOT
    assert subject.sha256(b"") == subject.EMPTY_ROOT


def test_a_single_leaf_is_its_own_root() -> None:
    assert subject.Tree([b"only"]).root() == leaf_hash(b"only")


def test_the_baked_root_of_five_leaves() -> None:
    assert hex_of(subject.Tree(LEAVES).root()) == ROOT_FIVE


def test_leaf_order_changes_the_root() -> None:
    assert subject.Tree([b"a", b"b"]).root() != subject.Tree([b"b", b"a"]).root()


def test_every_index_of_every_small_size_verifies() -> None:
    for size in range(1, 25):
        leaves = [f"leaf-{number}".encode() for number in range(size)]
        built = subject.Tree(leaves)
        for index in range(size):
            proof = built.prove(index)
            assert len(proof.path) == subject.siblings_needed(index, size)
            verdict = subject.verify(index, leaves[index], proof.path,
                                     root=built.root(), size=size)
            assert verdict.ok, f"size {size} index {index}: {verdict.reason}"


def test_every_mutated_sibling_breaks_the_proof() -> None:
    built = subject.Tree(LEAVES)
    proof = built.prove(2)
    for position in range(len(proof.path)):
        path = list(proof.path)
        path[position] = leaf_hash(b"somebody else")
        verdict = subject.verify(2, LEAVES[2], tuple(path), root=built.root(), size=5)
        assert not verdict.ok, f"sibling {position} was accepted"


def test_a_proof_belongs_to_its_index() -> None:
    built = subject.Tree(LEAVES)
    proof = built.prove(3)
    for other in (0, 1, 2, 4):
        verdict = subject.verify(other, LEAVES[3], proof.path, root=built.root(), size=5)
        assert not verdict.ok, f"index {other} accepted another index's proof"


def test_a_proof_records_the_root_it_proves() -> None:
    built = subject.Tree(LEAVES)
    proof = built.prove(4)
    assert proof.root == built.root()
    assert proof.size == 5
    assert proof.leaf == hex_of(leaf_hash(LEAVES[4]))


def test_a_proof_round_trips_through_json() -> None:
    proof = subject.Tree(LEAVES).prove(1)
    assert subject.Proof.from_dict(proof.as_dict()) == proof


def test_a_payload_that_is_not_a_proof_is_refused() -> None:
    with pytest.raises(subject.TreeError, match="this is not a proof"):
        subject.Proof.from_dict({"index": 0})


def test_the_sibling_count_must_match_the_size() -> None:
    built = subject.Tree(LEAVES)
    proof = built.prove(3)
    short = subject.verify(3, LEAVES[3], proof.path[:-1], root=built.root(), size=5)
    assert not short.ok
    assert "needs 3" in short.reason
    long = subject.verify(3, LEAVES[3], (*proof.path, proof.path[0]), root=built.root(), size=5)
    assert not long.ok


def test_a_sibling_must_be_a_full_digest() -> None:
    built = subject.Tree(LEAVES)
    proof = built.prove(3)
    verdict = subject.verify(3, LEAVES[3], (b"x" * 31, *proof.path[1:]),
                             root=built.root(), size=5)
    assert not verdict.ok
    assert "not 32" in verdict.reason


def test_degenerate_sizes_answer_instead_of_crashing() -> None:
    empty = subject.verify(0, b"a", (), root=subject.EMPTY_ROOT, size=0)
    assert not empty.ok
    assert "no leaf" in empty.reason
    out_of_range = subject.verify(5, LEAVES[4], (), root=subject.EMPTY_ROOT, size=5)
    assert not out_of_range.ok
    assert "not in a tree" in out_of_range.reason


def test_proving_an_index_that_is_not_there_is_an_error() -> None:
    with pytest.raises(subject.TreeError, match="not in a tree"):
        subject.Tree(LEAVES).prove(5)
    with pytest.raises(subject.TreeError, match="not in a tree"):
        subject.Tree([]).prove(0)
