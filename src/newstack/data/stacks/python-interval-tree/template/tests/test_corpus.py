from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    CorpusError,
    load_spans,
    synthetic,
    write_spans,
)
from {{ package_name }}.span import Interval


def test_a_written_list_reads_back(tmp_path) -> None:
    path = tmp_path / "spans.txt"
    spans = [Interval(-4, 2), Interval(0, 6), Interval(6, 9)]
    write_spans(spans, path)
    assert load_spans(path) == spans


def test_blanks_and_comments_are_skipped(tmp_path) -> None:
    path = tmp_path / "spans.txt"
    path.write_text("# note\n\n1 4\n\n5 8\n", encoding="utf-8")
    assert load_spans(path) == [Interval(1, 4), Interval(5, 8)]


def test_a_missing_file_is_named(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_spans(tmp_path / "gone.txt")


def test_words_are_refused(tmp_path) -> None:
    path = tmp_path / "spans.txt"
    path.write_text("two nine\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_spans(path)
    empty = tmp_path / "empty.txt"
    empty.write_text("# nothing\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_spans(empty)


def test_the_generator_is_seeded_and_stable() -> None:
    first = synthetic(40, seed=7)
    assert first == synthetic(40, seed=7)
    assert first != synthetic(40, seed=8)
    assert all(span.start < span.end for span in first)


def test_an_impossible_corpus_is_refused() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)
    with pytest.raises(CorpusError):
        synthetic(4, low=5, high=5)
    with pytest.raises(CorpusError):
        synthetic(4, widest=1)
