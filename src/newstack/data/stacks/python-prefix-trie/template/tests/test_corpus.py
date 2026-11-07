from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_words,
    synthetic,
    write_words,
)

SEEDS = (7, 23, 91, 1009)


def test_the_generator_is_deterministic_and_distinct() -> None:
    for seed in SEEDS:
        corpus = synthetic(80, seed=seed)
        assert corpus == synthetic(80, seed=seed)
        assert len(set(corpus)) == 80
        assert corpus == sorted(corpus)
        assert all(word.isascii() and word.isalpha() for word in corpus)


def test_a_corpus_of_zero_is_no_corpus() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)
    with pytest.raises(CorpusError):
        synthetic(-4)


def test_a_written_list_reads_back(tmp_path) -> None:
    corpus = synthetic(40, seed=9)
    path = str(tmp_path / "words.txt")
    write_words(corpus, path)
    assert load_words(path) == corpus


def test_comments_and_blanks_are_skipped(tmp_path) -> None:
    path = tmp_path / "words.txt"
    path.write_text("# a comment\n\ncar\n  cart  \n\n", encoding="utf-8")
    assert load_words(str(path)) == ["car", "cart"]


def test_a_broken_list_is_refused_by_name(tmp_path) -> None:
    noise = tmp_path / "noise.txt"
    noise.write_text("car\nCart\n", encoding="utf-8")
    with pytest.raises(CorpusError, match="word list"):
        load_words(str(noise))
    empty = tmp_path / "empty.txt"
    empty.write_text("# nothing\n", encoding="utf-8")
    with pytest.raises(CorpusError, match="no words"):
        load_words(str(empty))
    with pytest.raises(CorpusError, match="no such word list"):
        load_words(str(tmp_path / "missing.txt"))


def test_a_snapshot_replays_its_words_and_seed() -> None:
    corpus = synthetic(30, seed=4)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert thawed.words == tuple(corpus)
    assert thawed.seed == DEFAULT_SEED
    assert frozen == thawed


def test_half_a_snapshot_is_no_snapshot() -> None:
    for broken in ('{"seed": 1}', '{"words": ["ca"]}', "not json"):
        with pytest.raises(CorpusError):
            Snapshot.loads(broken)
