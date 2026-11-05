"""Chunking decides what the index can ever find, so pin the boundaries."""

from __future__ import annotations

import pytest

from {{ package_name }} import chunk as subject

TEXT = " ".join(f"w{index}" for index in range(100))


def test_a_long_document_is_split_into_overlapping_windows() -> None:
    chunks = subject.chunk_document("doc.md", TEXT, size=40, overlap=10)
    assert [chunk.start for chunk in chunks] == [0, 30, 60]
    assert chunks[-1].end == 100


def test_windows_together_cover_every_word_exactly_once_at_the_edges() -> None:
    chunks = subject.chunk_document("doc.md", TEXT, size=40, overlap=10)
    assert subject.uncovered("doc.md", TEXT, chunks) == []


def test_a_gap_in_the_windows_is_reported() -> None:
    chunks = subject.chunk_document("doc.md", TEXT, size=40, overlap=10)
    gapped = [chunk for chunk in chunks if chunk.start != 30]
    assert subject.uncovered("doc.md", TEXT, gapped) == list(range(40, 60))


def test_a_short_document_is_one_chunk() -> None:
    chunks = subject.chunk_document("short.md", "rotate the key", size=40, overlap=10)
    assert len(chunks) == 1
    assert (chunks[0].start, chunks[0].end) == (0, 3)


def test_the_chunk_id_is_the_document_and_the_offset() -> None:
    chunks = subject.chunk_document("doc.md", TEXT, size=40, overlap=10)
    assert [chunk.chunk_id for chunk in chunks] == ["doc.md#0", "doc.md#30", "doc.md#60"]


def test_chunking_is_deterministic() -> None:
    first = subject.chunk_document("doc.md", TEXT)
    second = subject.chunk_document("doc.md", TEXT)
    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]


def test_an_empty_document_produces_nothing() -> None:
    assert subject.chunk_document("empty.md", "  \n ") == []


@pytest.mark.parametrize(
    ("size", "overlap"),
    [(0, 0), (40, -1), (20, 20), (20, 25)],
)
def test_impossible_windows_are_refused(size: int, overlap: int) -> None:
    with pytest.raises(ValueError):
        subject.chunk_document("doc.md", TEXT, size=size, overlap=overlap)


def test_punctuation_does_not_make_words() -> None:
    assert subject.words("rotate-key.md: yes!") == ["rotate", "key", "md", "yes"]


def test_a_corpus_is_chunked_in_a_stable_order() -> None:
    documents = {"b.md": TEXT, "a.md": TEXT}
    chunks = subject.chunk_corpus(documents, size=40, overlap=10)
    assert next(chunk.doc_id for chunk in chunks) == "a.md"
    assert len(chunks) == 6
