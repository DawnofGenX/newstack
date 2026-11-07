from __future__ import annotations

from pathlib import Path

from {{ package_name }}.coder import (
    audit,
    compress,
    decompress,
)
from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_texts,
    report_lines,
    synthetic,
    write_texts,
)

CORPUS = Path(__file__).resolve().parent.parent / "fixtures" / "corpora.txt"


def test_the_generator_is_deterministic() -> None:
    assert synthetic(12, seed=7) == synthetic(12, seed=7)
    assert len(set(synthetic(12, seed=7))) == 12
    try:
        synthetic(0)
    except CorpusError:
        return
    raise AssertionError("zero texts were generated")


def test_a_snapshot_replays_its_texts() -> None:
    frozen = Snapshot(tuple(synthetic(6, seed=3)), DEFAULT_SEED)
    assert list(Snapshot.loads(frozen.dumps()).texts) == synthetic(6, seed=3)
    try:
        Snapshot.loads('{"seed": 1}')
    except CorpusError:
        return
    raise AssertionError("half a snapshot thawed")


def test_a_written_corpus_reads_back(tmp_path: Path) -> None:
    texts = synthetic(8, seed=11)
    path = str(tmp_path / "corpora.txt")
    write_texts(texts, path)
    assert load_texts(path) == texts


def test_a_noisy_corpus_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "noise.txt"
    path.write_text("# comment\n\nAbra\n", encoding="utf-8")
    try:
        load_texts(str(path))
    except CorpusError:
        return
    raise AssertionError("a noisy corpus was loaded")


def test_the_shipped_fixture_closes_the_loop(tmp_path: Path) -> None:
    texts = load_texts(str(CORPUS))
    assert len(texts) >= 8
    for text in texts:
        tokens = compress(text)
        assert decompress(tokens) == text
        assert audit(tokens) == []
        assert len(tokens) < len(text)


def test_the_report_prices_every_text() -> None:
    assert len(report_lines(["abra", "cadabra"])) == 2
