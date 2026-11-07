from __future__ import annotations

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_patterns,
    synthetic,
    write_patterns,
)


def test_the_generator_is_deterministic() -> None:
    assert synthetic(12, seed=7) == synthetic(12, seed=7)
    assert synthetic(12, seed=7) != synthetic(12, seed=8)
    assert len(set(synthetic(12))) == 12


def test_the_generator_refuses_nothing_counts() -> None:
    try:
        synthetic(0)
    except CorpusError:
        return
    raise AssertionError("zero patterns slipped through")


def test_a_written_list_reads_back(tmp_path) -> None:
    patterns = synthetic(9, seed=3)
    path = tmp_path / "patterns.txt"
    write_patterns(patterns, str(path))
    assert load_patterns(str(path)) == patterns


def test_noise_and_absence_are_named(tmp_path) -> None:
    try:
        load_patterns(str(tmp_path / "missing.txt"))
    except CorpusError:
        pass
    else:
        raise AssertionError("a missing list slipped through")
    noise = tmp_path / "noise.txt"
    noise.write_text("# comment\n\nAbra\n", encoding="utf-8")
    try:
        load_patterns(str(noise))
    except CorpusError:
        return
    raise AssertionError("a noisy list slipped through")


def test_a_snapshot_replays_its_patterns() -> None:
    patterns = synthetic(6, seed=4)
    frozen = Snapshot(tuple(patterns), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert thawed.patterns == tuple(patterns)
    assert thawed.seed == DEFAULT_SEED


def test_half_a_snapshot_is_no_snapshot() -> None:
    try:
        Snapshot.loads('{"seed": 1}')
    except CorpusError:
        return
    raise AssertionError("half a snapshot slipped through")
