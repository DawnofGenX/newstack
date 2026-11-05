from __future__ import annotations

import json

import pytest

from {{ package_name }} import journal
from {{ package_name }}.journal import Journal, JournalError


def test_a_missing_journal_reads_as_empty(tmp_path):
    assert journal.read(tmp_path / "none.jsonl") == []


def test_an_empty_file_reads_as_empty(tmp_path):
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    assert journal.read(empty) == []


def test_records_survive_a_round_trip(tmp_path):
    path = tmp_path / "journal.jsonl"
    log = Journal(path)
    log.append("trip", "saga.started", steps=["a", "b"])
    log.append("trip", "step.started", step="a", key="trip:a", attempt=1)
    records = journal.read(path)
    assert [record["seq"] for record in records] == [1, 2]
    assert records[1]["key"] == "trip:a"
    assert json.loads(path.read_text().splitlines()[1])["event"] == "step.started"


def test_a_torn_final_line_is_dropped(tmp_path):
    path = tmp_path / "torn.jsonl"
    path.write_text('{"seq": 1, "event": "saga.started", "saga": "s"}\n{"seq": 2, "eva')
    assert len(journal.read(path)) == 1


def test_a_torn_line_in_the_middle_is_refused(tmp_path):
    path = tmp_path / "broken.jsonl"
    path.write_text('{"seq": 1, "event": "saga.started", "saga": "s"}\n{"se\n{"seq": 3}\n')
    with pytest.raises(JournalError, match="line 2"):
        journal.read(path)


def test_a_line_that_is_not_a_record_is_refused(tmp_path):
    path = tmp_path / "odd.jsonl"
    path.write_text('{"seq": 1, "event": "saga.started", "saga": "s"}\n[1, 2, 3]\n')
    with pytest.raises(JournalError, match="not a journal record"):
        journal.read(path)


def test_an_unknown_event_is_refused(tmp_path):
    with pytest.raises(JournalError, match="mystery"):
        Journal(tmp_path / "x.jsonl").append("s", "step.danced")


def test_blank_lines_are_skipped(tmp_path):
    path = tmp_path / "space.jsonl"
    path.write_text('{"seq": 1, "event": "saga.started", "saga": "s"}\n\n\n')
    assert len(journal.read(path)) == 1


def test_records_are_keyed_by_saga(tmp_path):
    log = Journal(tmp_path / "j.jsonl")
    log.append("one", "saga.started")
    log.append("two", "saga.started")
    assert len(log.for_saga("one")) == 1
    assert log.outcome("one") is None


def test_the_last_saga_event_wins(tmp_path):
    log = Journal(tmp_path / "j.jsonl")
    log.append("s", "saga.started")
    log.append("s", "saga.completed")
    assert log.outcome("s") == "completed"


def test_statuses_track_the_last_word_on_each_step(tmp_path):
    log = Journal(tmp_path / "j.jsonl")
    log.append("s", "step.started", step="a", attempt=1)
    log.append("s", "step.failed", step="a", attempt=1, retryable=True)
    log.append("s", "step.started", step="a", attempt=2)
    log.append("s", "step.succeeded", step="a", attempt=2)
    log.append("s", "step.succeeded", step="b", attempt=1)
    log.append("s", "step.compensated", step="b", attempt=1)
    statuses = log.statuses("s")
    assert statuses == {"a": "succeeded", "b": "compensated"}


def test_an_interrupted_step_is_not_reported_as_succeeded(tmp_path):
    log = Journal(tmp_path / "j.jsonl")
    log.append("s", "step.started", step="a", attempt=1)
    assert log.statuses("s") == {"a": "interrupted"}
