from __future__ import annotations

import random

import pytest

from {{ package_name }}.btree import BTree
from {{ package_name }}.page import (
    PageError,
    page_pair,
    read_page,
    write_page,
)


def mixed_tree(order: int, seed: int) -> BTree:
    """A tree with a real insert AND delete history, not a clean build."""
    rng = random.Random(seed * 31 + order)
    tree = BTree(order)
    for _ in range(200):
        key = rng.randrange(-400, 400)
        if rng.random() < 0.55:
            tree.insert(key)
        else:
            tree.delete(key)
    return tree


def test_a_page_round_trip_survives_any_history(tmp_path) -> None:
    for order in (2, 3, 5):
        tree = mixed_tree(order, order)
        path = tmp_path / f"tree-{order}.page"
        report = page_pair(tree, path)
        assert report.identical is True
        clone = read_page(path)
        assert clone.keys == tree.keys
        assert [s.keys for s in clone.shape()] == [s.keys for s in tree.shape()]
        assert clone.order == tree.order


def test_a_rewrite_of_a_read_page_is_byte_identical(tmp_path) -> None:
    path = tmp_path / "tree.page"
    write_page(mixed_tree(3, 5), path)
    first = path.read_bytes()
    write_page(read_page(path), path)
    assert path.read_bytes() == first


def test_an_empty_tree_freezes_and_thaws(tmp_path) -> None:
    path = tmp_path / "empty.page"
    assert write_page(BTree(4), path) == 1
    assert read_page(path).keys == []


def test_the_record_width_follows_the_order() -> None:
    from {{ package_name }}.page import record_width

    small, large = record_width(2), record_width(5)
    assert large > small


def test_junk_is_refused_by_name(tmp_path) -> None:
    junk = tmp_path / "junk.page"
    junk.write_bytes(b"NOTAPAGE" + bytes(40))
    with pytest.raises(PageError):
        read_page(junk)


def test_a_short_file_is_refused(tmp_path) -> None:
    path = tmp_path / "short.page"
    write_page(BTree(3, range(20)), path)
    path.write_bytes(path.read_bytes()[:-4])
    with pytest.raises(PageError):
        read_page(path)


def test_a_missing_page_is_named(tmp_path) -> None:
    with pytest.raises(PageError):
        read_page(tmp_path / "gone.page")


def test_a_cloned_tree_still_behaves(tmp_path) -> None:
    tree = mixed_tree(3, 9)
    path = tmp_path / "live.page"
    write_page(tree, path)
    clone = read_page(path)
    for key in tree.keys[:5]:
        assert clone.lookup(key) is True
    assert clone.range_scan(-200, 200) == tree.range_scan(-200, 200)
    for key in range(-500, -490):
        clone.insert(key)
    assert clone.leaf_levels == 1
    assert clone.keys == sorted(set(tree.keys) | set(range(-500, -490)))
