"""A leaf and a node must not share a hash function."""

from __future__ import annotations

import pytest

from {{ package_name }} import hashing as subject


def test_a_leaf_carries_its_prefix() -> None:
    assert subject.leaf_hash(b"a") == subject.sha256(b"\x00a")
    assert subject.leaf_hash(b"a") != subject.sha256(b"a")


def test_a_node_carries_its_prefix_and_keeps_order() -> None:
    left, right = subject.leaf_hash(b"a"), subject.leaf_hash(b"b")
    assert subject.node_hash(left, right) == subject.sha256(b"\x01" + left + right)
    assert subject.node_hash(left, right) != subject.node_hash(right, left)


def test_a_node_digest_can_never_be_read_as_a_leaf_digest() -> None:
    left, right = subject.leaf_hash(b"a"), subject.leaf_hash(b"b")
    assert subject.node_hash(left, right) != subject.leaf_hash(left + right)


def test_a_node_needs_two_full_digests() -> None:
    with pytest.raises(subject.HashError, match="two 32-byte children"):
        subject.node_hash(b"short", subject.leaf_hash(b"b"))
    with pytest.raises(subject.HashError, match="two 32-byte children"):
        subject.node_hash(subject.leaf_hash(b"b"), b"")


def test_the_leaf_hash_is_baked_so_a_change_cannot_pass_quietly() -> None:
    assert subject.hex_of(subject.leaf_hash(b"entry-01")) == (
        "5bc0582d78fe58e0b498dd7f39a86b652ce8827e67ad85ad9ea255ec848c2177"
    )


def test_hex_round_trips() -> None:
    digest = subject.leaf_hash(b"round")
    assert subject.unhex(subject.hex_of(digest)) == digest
    assert subject.unhex("  " + subject.hex_of(digest) + "\n") == digest


def test_unhex_refuses_the_wrong_shape() -> None:
    with pytest.raises(subject.HashError, match="byte"):
        subject.unhex("ab")
    with pytest.raises(subject.HashError, match="not hexadecimal"):
        subject.unhex("z" * 64)
