from __future__ import annotations

import pytest

from {{ package_name }}.corpus import (
    DEFAULT_SEED,
    CorpusError,
    Record,
    Snapshot,
    audit,
    load_records,
    report_lines,
    synthetic,
    write_records,
)

FIXTURE = "fixtures/records.txt"


def test_the_generator_is_deterministic() -> None:
    assert synthetic(10) == synthetic(10)
    assert synthetic(10, seed=3) != synthetic(10, seed=4)


def test_zero_answers_no_records() -> None:
    with pytest.raises(CorpusError):
        synthetic(0)


def test_generated_records_audit_silent() -> None:
    for record in synthetic(25, seed=11):
        assert audit(record) == []


def test_a_record_carries_three_fields() -> None:
    record = Record("1 + 2", "1 2 +", 3)
    assert record.expr == "1 + 2"
    assert record.value == 3


@pytest.mark.parametrize(
    "noise",
    [
        lambda: Record("", "1 2 +", 3),
        lambda: Record("1 + 2", "", 3),
        lambda: Record("1 + 2", "1 2 +", "three"),
    ],
)
def test_a_broken_record_is_refused(noise) -> None:
    with pytest.raises(CorpusError):
        audit(noise())


def test_a_forged_answer_is_named() -> None:
    assert audit(Record("1 + 2", "1 2 +", 99))
    assert audit(Record("1 + 2", "1 + 2", 3))


def test_a_snapshot_replays_its_expressions() -> None:
    frozen = Snapshot(("1 + 2", "3 * 4"), DEFAULT_SEED)
    thawed = Snapshot.loads(frozen.dumps())
    assert thawed.exprs == ("1 + 2", "3 * 4")
    assert thawed.seed == DEFAULT_SEED


def test_half_a_snapshot_is_no_snapshot() -> None:
    with pytest.raises(CorpusError):
        Snapshot.loads('{"seed": 1}')


def test_a_ledger_writes_and_reads_back(tmp_path) -> None:
    corpus = synthetic(8, seed=5)
    path = str(tmp_path / "records.txt")
    write_records(corpus, path)
    assert load_records(path) == corpus


def test_a_missing_ledger_is_named(tmp_path) -> None:
    with pytest.raises(CorpusError):
        load_records(str(tmp_path / "missing.txt"))


def test_a_noisy_ledger_is_refused(tmp_path) -> None:
    noise = tmp_path / "noise.txt"
    noise.write_text("1 + 2 | junk\n", encoding="utf-8")
    with pytest.raises(CorpusError):
        load_records(str(noise))


def test_the_shipped_fixture_audits_silent() -> None:
    records = load_records(FIXTURE)
    assert len(records) >= 8
    assert all(audit(record) == [] for record in records)
    assert len(report_lines(records)) == len(records)
