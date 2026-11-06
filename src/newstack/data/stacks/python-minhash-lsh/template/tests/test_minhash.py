import pytest

from {{ package_name }} import minhash as subject
from {{ package_name }} import shingles as shingle_module

TEXT = "the quick brown fox jumps over the lazy dog and then goes home again"


def test_a_signature_has_one_value_per_position() -> None:
    assert len(subject.MinHash(64).signature(TEXT)) == 64


def test_the_same_text_signs_the_same_way() -> None:
    scheme = subject.MinHash(64)
    assert scheme.signature(TEXT) == scheme.signature(TEXT)


def test_a_document_matches_itself_exactly() -> None:
    scheme = subject.MinHash(64)
    signature = scheme.signature(TEXT)
    assert scheme.estimate(signature, signature) == 1.0


def test_the_signature_of_a_set_matches_the_signature_of_the_text() -> None:
    scheme = subject.MinHash(64, shingle_size=3)
    items = shingle_module.shingles(TEXT, 3)
    assert scheme.signature_of(items) == scheme.signature(TEXT)


def test_the_promised_deviation_is_one_over_root_width() -> None:
    assert subject.MinHash(256).error == pytest.approx(1 / 16)


def test_the_seed_changes_the_permutations() -> None:
    left = subject.MinHash(64, seed=1).signature(TEXT)
    right = subject.MinHash(64, seed=2).signature(TEXT)
    assert left != right


def test_the_estimate_is_a_fraction() -> None:
    scheme = subject.MinHash(128)
    other = "a completely different sentence about weather and the sea"
    estimate = scheme.estimate(scheme.signature(TEXT), scheme.signature(other))
    assert 0.0 <= estimate <= 1.0


def test_signatures_of_different_widths_are_not_comparable() -> None:
    with pytest.raises(subject.MinHashError, match="cannot be compared"):
        subject.MinHash(64).estimate(
            subject.MinHash(64).signature(TEXT), subject.MinHash(32).signature(TEXT)
        )


def test_a_width_below_one_is_refused() -> None:
    with pytest.raises(subject.MinHashError, match="at least one position"):
        subject.MinHash(0)


def test_a_shingle_size_below_one_is_refused() -> None:
    with pytest.raises(shingle_module.ShingleError, match="at least one word"):
        subject.MinHash(64, shingle_size=0).signature(TEXT)
