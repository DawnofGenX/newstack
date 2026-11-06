from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    CorpusError,
    dedupe,
    load_words,
    synthetic,
)
from {{ package_name }}.tree import BKTree


def test_blanks_and_comments_are_skipped(tmp_path) -> None:
    path = tmp_path / "words.txt"
    path.write_text("# a comment\nhello\n\nHELLO\nhello\n", encoding="utf-8")
    assert load_words(path) == ["hello", "HELLO", "hello"]
    assert load_words(path, lowercase=True) == ["hello", "hello", "hello"]


def test_a_missing_file_is_named(tmp_path) -> None:
    with pytest.raises(CorpusError, match="no such word list"):
        load_words(tmp_path / "missing.txt")


def test_a_file_without_words_is_refused(tmp_path) -> None:
    path = tmp_path / "empty.txt"
    path.write_text("# nothing but a comment\n", encoding="utf-8")
    with pytest.raises(CorpusError, match="holds no words"):
        load_words(path)


def test_dedupe_keeps_the_first_of_each() -> None:
    assert dedupe(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]


def test_the_generator_is_a_fixed_order_for_a_fixed_seed() -> None:
    assert synthetic(40, seed=7) == synthetic(40, seed=7)
    assert synthetic(40, seed=7) != synthetic(40, seed=8)


def test_a_corpus_of_zero_words_is_not_a_corpus() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)


def test_a_seeded_tree_holds_every_word_once() -> None:
    words = synthetic(200, seed=5)
    tree = BKTree(words)
    assert len(tree) == 200
    assert tree.add(words[10]) is False
    assert len(tree) == 200


def test_a_tree_only_accepts_words() -> None:
    tree = BKTree()
    with pytest.raises(ValueError, match="strings"):
        tree.add(7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="empty string"):
        tree.add("")


def test_membership_never_raises() -> None:
    tree = BKTree(["hello"])
    assert "hello" in tree
    assert "help" not in tree
    assert 7 not in tree
