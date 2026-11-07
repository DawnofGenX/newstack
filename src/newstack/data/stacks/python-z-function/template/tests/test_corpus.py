from __future__ import annotations

from tempfile import TemporaryDirectory

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_words,
    synthetic,
    write_words,
)


def test_the_generator_is_deterministic() -> None:
    assert synthetic(12, seed=3) == synthetic(12, seed=3)
    assert synthetic(12, seed=3) != synthetic(12, seed=4)
    assert len(set(synthetic(12, seed=3))) == 12


def test_no_words_from_zero() -> None:
    try:
        synthetic(0)
    except CorpusError:
        return
    raise AssertionError("zero made words")


def test_a_written_list_reads_back() -> None:
    words = synthetic(8, seed=11)
    with TemporaryDirectory() as room:
        path = f"{room}/words.txt"
        write_words(words, path)
        assert load_words(path) == words


def test_a_missing_list_is_named() -> None:
    try:
        load_words("/no/such/words.txt")
    except CorpusError:
        return
    raise AssertionError("a missing list answered")


def test_a_noisy_list_is_refused() -> None:
    with TemporaryDirectory() as room:
        path = f"{room}/noise.txt"
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("# comment\n\nAbra\n")
        try:
            load_words(path)
        except CorpusError:
            return
        raise AssertionError("noise passed the gate")


def test_a_snapshot_replays_its_words() -> None:
    words = synthetic(6, seed=2)
    frozen = Snapshot(tuple(words), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert list(thawed.words) == words
    assert thawed.seed == DEFAULT_SEED


def test_half_a_snapshot_is_no_snapshot() -> None:
    for broken in ('{"seed": 1}', '{"words": ["Abra"], "seed": 1}', "not json"):
        try:
            Snapshot.loads(broken)
        except CorpusError:
            continue
        raise AssertionError(f"{broken!r} thawed")
