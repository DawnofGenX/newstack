from __future__ import annotations

from tempfile import TemporaryDirectory

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_texts,
    report_lines,
    synthetic,
    write_texts,
)
from {{ package_name }}.rle import (
    decode,
    encode,
)


def test_the_generator_is_deterministic() -> None:
    assert synthetic(10, seed=7) == synthetic(10, seed=7)
    assert len(synthetic(10, seed=7)) == 10
    assert len(set(synthetic(10, seed=7))) == 10


def test_the_generator_refuses_no_texts() -> None:
    try:
        synthetic(0)
    except CorpusError:
        return
    raise AssertionError("zero texts were generated")


def test_a_snapshot_replays_its_texts() -> None:
    frozen = Snapshot(tuple(synthetic(5, seed=3)), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert list(thawed.texts) == synthetic(5, seed=3)
    assert thawed.seed == DEFAULT_SEED


def test_half_a_snapshot_is_no_snapshot() -> None:
    try:
        Snapshot.loads('{"seed": 1}')
    except CorpusError:
        return
    raise AssertionError("half a snapshot thawed")


def test_a_written_corpus_reads_back() -> None:
    corpus = synthetic(6, seed=11)
    with TemporaryDirectory() as room:
        path = f"{room}/corpora.txt"
        write_texts(corpus, path)
        assert load_texts(path) == corpus


def test_a_missing_corpus_is_named() -> None:
    with TemporaryDirectory() as room:
        try:
            load_texts(f"{room}/missing.txt")
        except CorpusError:
            return
    raise AssertionError("a missing corpus answered")


def test_a_noisy_corpus_is_refused() -> None:
    with TemporaryDirectory() as room:
        path = f"{room}/noise.txt"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("# a comment\n\nAbra\n")
        try:
            load_texts(path)
        except CorpusError:
            return
    raise AssertionError("a noisy corpus loaded")


def test_a_corpus_without_texts_is_refused() -> None:
    with TemporaryDirectory() as room:
        path = f"{room}/quiet.txt"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("# nothing here\n\n")
        try:
            load_texts(path)
        except CorpusError:
            return
    raise AssertionError("an empty corpus answered")


def test_the_report_counts_every_text() -> None:
    texts = ["abra", "aabb"]
    lines = report_lines(texts)
    assert len(lines) == 2
    for line, text in zip(lines, texts, strict=False):
        assert line.startswith(f"{len(text)} letters -> {len(encode(text))} pairs")
        assert decode(encode(text)) == text
