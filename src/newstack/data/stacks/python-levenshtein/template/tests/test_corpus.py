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


def test_the_generator_is_deterministic_and_distinct() -> None:
    assert synthetic(60, seed=5) == synthetic(60, seed=5)
    words = synthetic(60, seed=5)
    assert len(set(words)) == 60
    assert words == sorted(words)


def test_a_corpus_of_zero_is_no_corpus() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)


def test_a_written_list_reads_back(tmp_path) -> None:
    corpus = synthetic(40, seed=11)
    path = tmp_path / "words.txt"
    write_words(corpus, str(path))
    assert load_words(str(path)) == corpus


def test_a_missing_list_is_named(tmp_path) -> None:
    with pytest.raises(CorpusError, match="no such word list"):
        load_words(str(tmp_path / "missing.txt"))


def test_comments_and_blanks_are_skipped_noise_is_refused(tmp_path) -> None:
    path = tmp_path / "mixed.txt"
    path.write_text("# a comment\n\ncar\n\n# end\n", encoding="utf-8")
    assert load_words(str(path)) == ["car"]
    noise = tmp_path / "noise.txt"
    noise.write_text("# comment\n\nCart\n", encoding="utf-8")
    with pytest.raises(CorpusError, match="word list holds"):
        load_words(str(noise))
    empty = tmp_path / "empty.txt"
    empty.write_text("# nothing\n", encoding="utf-8")
    with pytest.raises(CorpusError, match="holds no words"):
        load_words(str(empty))


def test_a_snapshot_replays_its_words_and_seed() -> None:
    corpus = synthetic(30, seed=7)
    frozen = Snapshot(tuple(corpus), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert list(thawed.words) == corpus
    assert thawed.seed == DEFAULT_SEED


def test_half_a_snapshot_is_no_snapshot() -> None:
    with pytest.raises(CorpusError, match="half a snapshot"):
        Snapshot.loads('{"seed": 1}')
