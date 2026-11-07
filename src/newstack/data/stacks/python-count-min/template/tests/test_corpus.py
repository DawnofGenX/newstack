from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Snapshot,
    load_stream,
    synthetic,
    write_stream,
)


def test_the_generator_is_deterministic(tmp_path) -> None:
    assert synthetic(20) == synthetic(20)
    assert synthetic(20, seed=5) != synthetic(20, seed=6)
    events = synthetic(30, seed=11)
    assert len(events) == 30
    assert all(0 <= key < 256 and n > 0 for key, n in events)


def test_no_events_from_zero() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)


def test_a_stream_round_trips(tmp_path) -> None:
    events = synthetic(12, seed=3)
    path = tmp_path / "stream.txt"
    write_stream(events, str(path))
    assert load_stream(str(path)) == events


def test_blank_lines_and_comments_are_skipped(tmp_path) -> None:
    path = tmp_path / "stream.txt"
    path.write_text("# a comment\n\n7 2\n", encoding="utf-8")
    assert load_stream(str(path)) == [(7, 2)]


def test_noise_is_refused(tmp_path) -> None:
    for body in ("7.5\n", "7\n", "7 2 3\n", "7 0\n", "300 1\n", "\n"):
        path = tmp_path / "noise.txt"
        path.write_text(body, encoding="utf-8")
        with pytest.raises(CorpusError):
            load_stream(str(path))


def test_a_missing_stream_is_named(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_stream(str(tmp_path / "missing.txt"))


def test_a_snapshot_replays_its_events() -> None:
    events = tuple(synthetic(10, seed=9))
    frozen = Snapshot(events, DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert list(thawed.events) == list(events)
    assert thawed.seed == DEFAULT_SEED


def test_half_a_snapshot_is_no_snapshot() -> None:
    for body in ('{"seed": 1}', "not json", '{"events": [[7]], "seed": 1}'):
        with pytest.raises(CorpusError):
            Snapshot.loads(body)
