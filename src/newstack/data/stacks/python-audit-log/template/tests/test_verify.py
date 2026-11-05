"""The chain, the checkpoint, and the attack that beats the chain but not the checkpoint."""

from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }} import demo as demo_mod
from {{ package_name }} import store as store_mod
from {{ package_name }} import verify as subject


def seeded(tmp_path: Path, count: int = 3) -> store_mod.Store:
    store = store_mod.Store(tmp_path / "log.db")
    for index in range(1, count + 1):
        store.append(actor="alice", action="note.update", target=f"note/{index}")
    return store


def test_a_clean_log_verifies(tmp_path: Path) -> None:
    store = seeded(tmp_path)
    try:
        report = subject.verify(store)
    finally:
        store.close()
    assert report.ok
    assert report.count == 3
    assert report.head_seq == 3
    assert report.problems == ()


def test_an_empty_log_is_not_broken(tmp_path: Path) -> None:
    store = store_mod.Store(tmp_path / "log.db")
    try:
        report = subject.verify(store)
    finally:
        store.close()
    assert report.ok
    assert report.count == 0


def test_an_edited_body_is_named_and_located(tmp_path: Path) -> None:
    store = seeded(tmp_path)
    try:
        demo_mod.edit_body(store, 2, {"note": "I was never here"})
        report = subject.verify(store)
    finally:
        store.close()
    assert not report.ok
    problem = report.problems[0]
    assert (problem.seq, problem.kind) == (2, "body-changed")
    assert "now hashes to" in problem.message


def test_an_edit_is_caught_at_its_own_row_and_not_by_the_next_link(tmp_path: Path) -> None:
    """The stored hash column is untouched, so event 3 still links to event 2. That is the point:
    a chain proves the links, and the links alone never prove the prose."""
    store = seeded(tmp_path)
    try:
        demo_mod.edit_body(store, 2, {"note": "I was never here"})
        report = subject.verify(store)
    finally:
        store.close()
    assert [problem.kind for problem in report.problems] == ["body-changed"]


def test_a_deleted_row_is_a_gap(tmp_path: Path) -> None:
    store = seeded(tmp_path)
    try:
        demo_mod.delete_event(store, 2)
        problems = subject.verify(store).problems
    finally:
        store.close()
    assert any(problem.kind == "gap" for problem in problems)


def test_a_checkpoint_notices_truncation(tmp_path: Path) -> None:
    store = seeded(tmp_path)
    try:
        checkpoint = subject.checkpoint_of(store)
        demo_mod.delete_event(store, 3)
        report = subject.verify(store, checkpoint)
    finally:
        store.close()
    assert any(problem.kind == "truncated" for problem in report.problems)


def test_appending_after_a_checkpoint_is_not_a_failure(tmp_path: Path) -> None:
    store = seeded(tmp_path)
    try:
        checkpoint = subject.checkpoint_of(store)
        store.append(actor="bob", action="note.update", target="note/4")
        report = subject.verify(store, checkpoint)
    finally:
        store.close()
    assert report.ok
    assert report.head_seq == 4


def test_a_full_rewrite_beats_the_chain_and_loses_to_the_checkpoint(tmp_path: Path) -> None:
    store = seeded(tmp_path)
    try:
        checkpoint = subject.checkpoint_of(store)
        demo_mod.rebuild_chain(store)
        assert subject.verify(store).ok
        guarded = subject.verify(store, checkpoint)
    finally:
        store.close()
    assert not guarded.ok
    assert guarded.problems[0].kind == "rewritten"


def test_a_checkpoint_round_trips_through_a_file(tmp_path: Path) -> None:
    store = seeded(tmp_path)
    try:
        original = subject.checkpoint_of(store)
        original.save(tmp_path / "head.json")
        loaded = subject.Checkpoint.load(tmp_path / "head.json")
    finally:
        store.close()
    assert loaded == original


@pytest.mark.parametrize("text", ["", "{", '{"format": 2}', '{"format": 1}'])
def test_a_broken_checkpoint_file_is_refused(tmp_path: Path, text: str) -> None:
    path = tmp_path / "head.json"
    path.write_text(text)
    with pytest.raises(ValueError):
        subject.Checkpoint.load(path)


def test_a_missing_checkpoint_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="cannot read"):
        subject.Checkpoint.load(tmp_path / "absent.json")


def test_an_unknown_problem_kind_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown problem kind"):
        subject.Problem(1, "vibes", "not a thing")
