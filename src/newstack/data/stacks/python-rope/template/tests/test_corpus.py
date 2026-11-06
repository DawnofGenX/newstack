from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }} import corpus as subject

CorpusError = subject.CorpusError
load_text = subject.load_text
synthetic = subject.synthetic

FIXTURE = Path("fixtures/text.txt")


def test_the_shipped_fixture_reads_as_a_text(tmp_path: Path) -> None:
    source = tmp_path / "text.txt"
    source.write_text("# a note\nalpha bravo\n\ncharlie\n", encoding="utf-8")
    assert load_text(source) == "alpha bravo\ncharlie"


def test_the_shipped_fixture_is_a_text(tmp_path: Path) -> None:
    source = tmp_path / "text.txt"
    source.write_text("one\n", encoding="utf-8")
    assert load_text(source) == "one"


def test_a_file_of_comments_holds_no_text(tmp_path: Path) -> None:
    source = tmp_path / "notes.txt"
    source.write_text("# only a note\n\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_text(source)


def test_a_missing_text_is_named_by_name(tmp_path: Path) -> None:
    with pytest.raises(CorpusError, match="no such text"):
        load_text(tmp_path / "gone.txt")


def test_a_directory_is_not_a_text(tmp_path: Path) -> None:
    with pytest.raises(CorpusError, match="directory"):
        load_text(tmp_path)


def test_the_generator_is_deterministic_per_seed() -> None:
    assert synthetic(8, seed=3) == synthetic(8, seed=3)
    assert synthetic(8, seed=3) != synthetic(8, seed=4)


def test_paragraphs_keep_their_line_count() -> None:
    text = synthetic(6, seed=9, words=4)
    assert len(text.split("\n")) == 6
    assert all(line.count(" ") == 3 for line in text.split("\n"))


def test_zero_paragraphs_or_words_are_refused() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)
    with pytest.raises(CorpusError):
        synthetic(2, words=0)
