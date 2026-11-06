import pytest

from {{ package_name }} import shingles as subject


def test_normalize_folds_case_and_punctuation() -> None:
    assert subject.normalize("The Quick, BROWN fox!") == "the quick brown fox"


def test_a_shingle_window_covers_the_document() -> None:
    items = subject.shingles("a b c d e f", 5)
    assert items == frozenset({"a b c d e", "b c d e f"})


def test_a_short_document_is_its_own_shingle() -> None:
    assert subject.shingles("a b", 5) == frozenset({"a b"})


def test_the_same_words_in_another_case_are_the_same_set() -> None:
    assert subject.shingles("The cat sat", 2) == subject.shingles("the  cat, sat!", 2)


def test_jaccard_of_identical_sets_is_one() -> None:
    left = subject.shingles("the quick brown fox jumps", 3)
    assert subject.jaccard(left, left) == 1.0


def test_jaccard_of_disjoint_sets_is_zero() -> None:
    assert subject.jaccard(subject.shingles("a b c", 3), subject.shingles("x y z", 3)) == 0.0


def test_jaccard_is_symmetric() -> None:
    left = subject.shingles("a b c d e f", 3)
    right = subject.shingles("a b c x y z", 3)
    assert subject.jaccard(left, right) == subject.jaccard(right, left)


def test_a_single_word_shingle_separates_phrases() -> None:
    assert subject.shingles("cat", 1) != subject.shingles("the cat", 1)


def test_a_shingle_size_below_one_is_refused() -> None:
    with pytest.raises(subject.ShingleError, match="at least one word"):
        subject.shingles("a b c", 0)


def test_empty_text_is_refused() -> None:
    with pytest.raises(subject.ShingleError, match="no words"):
        subject.shingles("   ", 3)
