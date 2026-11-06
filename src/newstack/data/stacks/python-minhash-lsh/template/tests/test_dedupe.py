import pytest

from {{ package_name }} import dedupe as subject
from {{ package_name }} import lsh as lsh_module
from {{ package_name }} import minhash as minhash_module

TEXTS = {
    "a": "the quick brown fox jumps over the lazy dog and then goes home again",
    "b": "the quick brown fox jumps over the lazy dog and then goes home again",
    "c": "a completely different sentence about weather and the sea",
}


def _signatures(width: int = 128) -> dict[str, tuple[int, ...]]:
    scheme = minhash_module.MinHash(width)
    return {name: scheme.signature(text) for name, text in TEXTS.items()}


def test_the_identical_pair_is_clustered() -> None:
    groups = subject.cluster(_signatures(), lsh_module.Bands(16, 8), threshold=0.5)
    assert any({"a", "b"} <= set(group) for group in groups.clusters)


def test_the_unrelated_document_stands_alone() -> None:
    groups = subject.cluster(_signatures(), lsh_module.Bands(16, 8), threshold=0.5)
    assert all(len(group) == 1 for group in groups.clusters if "c" in group)


def test_every_document_appears_exactly_once() -> None:
    groups = subject.cluster(_signatures(), lsh_module.Bands(16, 8), threshold=0.5)
    seen = [name for group in groups.clusters for name in group]
    assert sorted(seen) == sorted(TEXTS)


def test_one_duplicate_is_counted() -> None:
    groups = subject.cluster(_signatures(), lsh_module.Bands(16, 8), threshold=0.5)
    assert groups.duplicates == 1


def test_a_pair_below_the_threshold_is_rejected() -> None:
    left = tuple(range(128))
    right = (1, *tuple(range(1, 128)))
    groups = subject.cluster({"a": left, "b": right}, lsh_module.Bands(8, 16), threshold=0.999)
    assert groups.joined == 0
    assert groups.rejected == 1


def test_an_empty_clustering_is_refused() -> None:
    with pytest.raises(subject.DedupeError, match="nothing to cluster"):
        subject.cluster({}, lsh_module.Bands(8, 16))


def test_a_threshold_outside_zero_to_one_is_refused() -> None:
    with pytest.raises(subject.DedupeError, match=r"0\.\.1"):
        subject.cluster(_signatures(), lsh_module.Bands(16, 8), threshold=2.0)


def test_a_signature_shorter_than_the_banding_is_refused() -> None:
    with pytest.raises(lsh_module.LshError, match=r"position\(s\)"):
        subject.cluster(_signatures(32), lsh_module.Bands(8, 16))
