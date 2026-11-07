from __future__ import annotations

from {{ package_name }}.coder import decode, encode
from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_texts,
    report_lines,
    synthetic,
    write_texts,
)
from {{ package_name }}.freq import tally
from {{ package_name }}.table import (
    audit,
    code_table,
)

FIXTURE = "fixtures/corpora.txt"


def test_the_shipped_fixture_closes_the_loop_price_by_price() -> None:
    for text in load_texts(FIXTURE):
        book = code_table(tally(text))
        assert decode(encode(text, book), book) == text
        assert audit(book) == []


def test_a_skewed_fixture_text_pays_under_eight_bits_a_letter() -> None:
    for text in load_texts(FIXTURE):
        book = code_table(tally(text))
        assert len(encode(text, book)) < len(text) * 8


def test_load_texts_skips_blanks_and_comments(tmp_path) -> None:
    corpus = tmp_path / "corpus.txt"
    corpus.write_text("# a comment\n\nbanana\n\n# done\n", encoding="utf-8")
    assert load_texts(str(corpus)) == ["banana"]


def test_a_missing_or_empty_corpus_is_refused(tmp_path) -> None:
    for path in (str(tmp_path / "missing.txt"),):
        try:
            load_texts(path)
        except CorpusError:
            continue
        raise AssertionError("a missing corpus names no texts")
    blank = tmp_path / "blank.txt"
    blank.write_text("# nothing\n", encoding="utf-8")
    try:
        load_texts(str(blank))
    except CorpusError:
        return
    raise AssertionError("a corpus of comments names no texts")


def test_write_and_read_a_corpus_round_trips(tmp_path) -> None:
    texts = synthetic(5)
    path = tmp_path / "corpus.txt"
    write_texts(texts, str(path))
    assert load_texts(str(path)) == texts


def test_synthetic_corpora_are_deterministic_and_skewed() -> None:
    assert synthetic(8) == synthetic(8, seed=DEFAULT_SEED)
    assert synthetic(4, seed=7) != synthetic(4, seed=11)
    for text in synthetic(10):
        book = code_table(tally(text))
        assert decode(encode(text, book), book) == text


def test_a_snapshot_freezes_and_thaws() -> None:
    texts = synthetic(3)
    frozen = Snapshot(tuple(texts), DEFAULT_SEED)
    assert Snapshot.loads(frozen.dumps()) == frozen


def test_the_report_prices_a_corpus_line_by_line() -> None:
    lines = report_lines(["banana", "mississippi"])
    assert len(lines) == 2
    assert all("letters ->" in line and "bits over" in line for line in lines)
