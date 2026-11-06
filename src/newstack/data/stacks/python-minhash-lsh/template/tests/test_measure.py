import pytest

from {{ package_name }} import corpus
from {{ package_name }} import lsh as lsh_module
from {{ package_name }} import measure as subject


def test_the_candidate_set_is_smaller_than_every_pair() -> None:
    documents = corpus.family(count=40, duplicates=20, replace_every=40)
    report = subject.evaluate(documents, width=128, bands=lsh_module.Bands(8, 16))
    assert report.candidates < report.all_pairs


def test_the_truth_finds_the_planted_duplicates() -> None:
    documents = corpus.family(count=40, duplicates=20, replace_every=40)
    report = subject.evaluate(documents, width=128, bands=lsh_module.Bands(8, 16))
    assert report.true_pairs >= 20


def test_every_candidate_pair_is_verified() -> None:
    documents = corpus.family(count=20, duplicates=10, replace_every=40)
    report = subject.evaluate(documents, width=128, bands=lsh_module.Bands(8, 16))
    assert report.verified == report.candidates


def test_recall_and_precision_are_fractions() -> None:
    documents = corpus.family(count=20, duplicates=10, replace_every=40)
    report = subject.evaluate(documents, width=128, bands=lsh_module.Bands(8, 16))
    assert 0.0 <= report.recall <= 1.0
    assert 0.0 <= report.precision <= 1.0


def test_fewer_bands_find_no_more_pairs() -> None:
    documents = corpus.family(count=30, duplicates=15, replace_every=40)
    wide = subject.evaluate(documents, width=128, bands=lsh_module.Bands(8, 16))
    narrow = subject.evaluate(documents, width=128, bands=lsh_module.Bands(4, 32))
    assert narrow.candidates <= wide.candidates


def test_the_spread_tracks_the_promise() -> None:
    base, edited, name = corpus.pair(replace_every=20)
    measured, promised, pairs = subject.estimate_spread(
        [(name, base), (f"{name}-edited", edited)], width=512
    )
    assert pairs == 1
    assert measured <= 2 * promised


def test_a_corpus_of_one_document_is_refused() -> None:
    with pytest.raises(ValueError, match="at least two documents"):
        subject.evaluate([("only", "a single document")], width=128)


def test_two_documents_sharing_a_name_are_refused() -> None:
    documents = [("same", "one document here"), ("same", "another document here")]
    with pytest.raises(ValueError, match="share a name"):
        subject.evaluate(documents, width=128)


def test_a_banding_wider_than_the_signature_is_refused() -> None:
    documents = corpus.family(count=4, duplicates=1, replace_every=40)
    with pytest.raises(ValueError, match="positions"):
        subject.evaluate(documents, width=32, bands=lsh_module.Bands(8, 16))
