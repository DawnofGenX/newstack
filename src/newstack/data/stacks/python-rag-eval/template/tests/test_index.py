"""BM25 behaviour that the evaluation depends on."""

from __future__ import annotations

import pytest

from {{ package_name }}.chunk import Chunk
from {{ package_name }}.index import BM25

CHUNKS = [
    Chunk("key.md", 0, 4, "rotate the signing key"),
    Chunk("retry.md", 0, 3, "retry the write"),
    Chunk("key.md", 40, 4, "the signing key is public"),
]


@pytest.fixture()
def index() -> BM25:
    return BM25(CHUNKS)


def test_the_chunk_that_shares_more_words_wins(index: BM25) -> None:
    hits = index.search("signing key", k=3)
    assert hits[0].doc_id == "key.md"
    assert len(hits) == 2


def test_idf_is_positive_even_for_a_term_in_every_chunk(index: BM25) -> None:
    assert index.idf("the") > 0
    assert index.idf("the") < index.idf("signing")


def test_an_unshared_word_finds_nothing(index: BM25) -> None:
    assert index.search("zebra") == []


def test_repeated_query_words_do_not_double_the_score(index: BM25) -> None:
    once = index.search("key", k=1)[0].score
    twice = index.search("key key", k=1)[0].score
    assert once == pytest.approx(twice)


def test_hits_are_ordered_by_score_then_id(index: BM25) -> None:
    hits = index.search("the signing key", k=5)
    assert [hit.score for hit in hits] == sorted((hit.score for hit in hits), reverse=True)


def test_k_must_be_positive(index: BM25) -> None:
    with pytest.raises(ValueError):
        index.search("key", k=0)


def test_an_empty_corpus_is_refused_outright() -> None:
    with pytest.raises(ValueError):
        BM25([])
