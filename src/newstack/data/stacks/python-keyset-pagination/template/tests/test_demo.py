"""The demo is a test: if a future change makes OFFSET safe, this fails."""

from __future__ import annotations

from pathlib import Path

from {{ package_name }} import demo as subject


def test_a_deletion_costs_the_offset_walk_a_row(tmp_path: Path) -> None:
    steps = subject.run(tmp_path)
    deletion = steps[0]
    assert deletion.keyset_clean
    assert deletion.offset_skipped >= 1
    assert deletion.offset_seen == deletion.rows - 1


def test_an_insertion_costs_the_offset_walk_a_repeat(tmp_path: Path) -> None:
    steps = subject.run(tmp_path)
    insertion = steps[1]
    assert insertion.keyset_clean
    assert insertion.offset_duplicated >= 1
    assert insertion.offset_seen > insertion.rows


def test_both_scenarios_render_a_verdict(tmp_path: Path) -> None:
    steps = subject.run(tmp_path)
    assert len(steps) == 2
    for step in steps:
        assert "cursor clean" in step.render()
        assert len(step.lines()) >= 2
