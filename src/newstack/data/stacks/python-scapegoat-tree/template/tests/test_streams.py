from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }}.streams import (
    Snapshot,
    StreamError,
    load_keys,
    synthetic,
    write_keys,
)


def test_one_seed_hands_one_stream() -> None:
    pairs = synthetic(24, seed=11)
    assert synthetic(24, seed=11) == pairs
    assert len({key for key, _ in pairs}) == 24


@pytest.mark.parametrize("count", [0, -1, True, "six"])
def test_a_stream_size_must_be_real(count: object) -> None:
    with pytest.raises(StreamError):
        synthetic(count)  # type: ignore[arg-type]


def test_a_written_stream_reads_back(tmp_path: Path) -> None:
    pairs = synthetic(12, seed=5)
    path = tmp_path / "keys.txt"
    write_keys(pairs, path)
    assert load_keys(path) == pairs


def test_blank_lines_and_comments_are_skipped(tmp_path: Path) -> None:
    path = tmp_path / "keys.txt"
    path.write_text("# header\n\n1 10\n\n2 20\n", encoding="utf-8")
    assert load_keys(path) == [(1, 10), (2, 20)]


def test_noise_in_the_stream_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "keys.txt"
    path.write_text("one two\n", encoding="utf-8")
    with pytest.raises(StreamError):
        load_keys(path)


def test_a_missing_stream_is_unusable(tmp_path: Path) -> None:
    with pytest.raises(StreamError):
        load_keys(tmp_path / "gone.txt")


def test_a_snapshot_replays_itself() -> None:
    pairs = synthetic(9, seed=3)
    frozen = Snapshot(pairs, 0.7)
    thawed = Snapshot.loads(frozen.dumps())
    assert thawed.pairs == pairs
    assert thawed.alpha == 0.7


@pytest.mark.parametrize("noise", ["[]", "{}", "not json"])
def test_a_noise_snapshot_is_refused(noise: str) -> None:
    with pytest.raises(StreamError):
        Snapshot.loads(noise)
