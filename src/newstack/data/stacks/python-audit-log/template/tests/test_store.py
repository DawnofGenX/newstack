"""The append-only table: sequence numbers, links, and one writer at a time."""

from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }} import store as subject


def test_appends_number_the_events_in_order(tmp_path: Path) -> None:
    with subject.Store(tmp_path / "log.db") as store:
        first = store.append(actor="alice", action="note.update", target="note/1")
        second = store.append(actor="bob", action="note.delete", target="note/2")
    assert (first.seq, second.seq) == (1, 2)
    assert second.prev_hash == first.hash


def test_the_head_is_the_last_event(tmp_path: Path) -> None:
    with subject.Store(tmp_path / "log.db") as store:
        store.append(actor="alice", action="a", target="t")
        head = store.append(actor="alice", action="a", target="t")
        assert store.head() is not None
        assert store.head().hash == head.hash
        assert store.count() == 2


def test_the_chain_survives_a_reopen(tmp_path: Path) -> None:
    path = tmp_path / "log.db"
    with subject.Store(path) as store:
        first = store.append(actor="alice", action="a", target="t")
    with subject.Store(path) as store:
        assert store.count() == 1
        second = store.append(actor="alice", action="a", target="t")
        assert second.seq == 2
        assert second.prev_hash == first.hash


def test_reads_are_ordered_by_sequence_not_by_time(tmp_path: Path) -> None:
    with subject.Store(tmp_path / "log.db") as store:
        store.append(actor="a", action="x", target="t", at="2026-11-05T10:00:02.000000+00:00")
        store.append(actor="a", action="x", target="t", at="2026-11-05T10:00:01.000000+00:00")
        stamps = [event.at for event in store.events()]
    assert stamps == sorted(stamps, reverse=True)


def test_a_limit_and_a_start_narrow_the_read(tmp_path: Path) -> None:
    with subject.Store(tmp_path / "log.db") as store:
        for index in range(1, 5):
            store.append(actor="a", action="x", target=f"t/{index}")
        assert [event.seq for event in store.events(limit=2)] == [1, 2]
        assert [event.seq for event in store.events(start=3)] == [3, 4]
        with pytest.raises(ValueError, match="limit must be at least 1"):
            store.events(limit=0)


def test_the_body_column_holds_canonical_json(tmp_path: Path) -> None:
    with subject.Store(tmp_path / "log.db") as store:
        store.append(actor="alice", action="a", target="t", detail={"z": 1, "a": 2})
        text = store.raw().execute("SELECT body FROM events WHERE seq = 1").fetchone()["body"]
    assert text.startswith('{"action":"a","actor":"alice","at":"')
    assert ',"detail":{"a":2,"z":1},' in text


def test_an_unopenable_path_is_reported(tmp_path: Path) -> None:
    with pytest.raises(subject.StoreError, match="cannot open"):
        subject.Store(tmp_path / "no-such-dir" / "log.db")
