from __future__ import annotations

import pytest

from {{ package_name }} import workload as subject
from {{ package_name }}.workload import (
    WorkloadError,
    run_stream,
    stream_matches,
)

REPLAY = subject.Replay


def test_the_shipped_stream_is_clean() -> None:
    for seed in (13, 77):
        replay = run_stream(seed=seed)
        assert replay.steps == 140
        assert replay.breaks == 0
        assert replay.seated
        assert replay.checks > replay.steps
        assert replay.clean


def test_a_narrow_grid_drifts_but_never_breaks() -> None:
    replay = run_stream(steps=60, seed=7, width=48, multipliers=(3, 5, 7, 11, 13))
    assert replay.breaks == 0
    assert replay.drift > 0
    assert replay.exact + replay.drift > 0


def test_the_shapes_answer_their_corpora_alike() -> None:
    assert stream_matches("shipped")
    assert stream_matches("narrow")


def test_a_stream_without_steps_is_refused() -> None:
    with pytest.raises(WorkloadError):
        run_stream(steps=0)


def test_a_replay_reports_its_ledger() -> None:
    replay = run_stream(steps=8, seed=4)
    assert REPLAY is subject.Replay
    assert replay.steps == 8
