"""The CLI: a gate for the scan, and a demo that must keep failing."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject
from {{ package_name }}.model import Order, Query
from {{ package_name }}.store import Store


def seed(tmp_path: Path, count: int = 30) -> Path:
    path = tmp_path / "items.db"
    with Store(path) as store:
        store.seed(count)
    return path


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    status = subject.main(list(argv))
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def test_seed_reports_what_it_created(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "--db", str(tmp_path / "x.db"), "seed", "--count", "5")
    assert status == 0
    assert "seeded 5 item(s)" in out


def test_a_page_prints_rows_and_a_cursor(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = seed(tmp_path)
    status, out, _ = run(capsys, "--db", str(db), "page", "--size", "7")
    assert status == 0
    assert len([line for line in out.splitlines() if line[:4].strip().isdigit()]) == 7
    assert "next " in out


def test_the_json_page_carries_the_cursor(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = seed(tmp_path)
    _, out, _ = run(capsys, "--db", str(db), "page", "--size", "7", "--json")
    payload = json.loads(out)
    assert payload["size"] == 7
    assert payload["next_cursor"]
    assert payload["query"]


def test_a_second_page_starts_where_the_first_ended(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = seed(tmp_path)
    _, out, _ = run(capsys, "--db", str(db), "page", "--size", "7", "--json")
    cursor = json.loads(out)["next_cursor"]
    _, out, _ = run(capsys, "--db", str(db), "page", "--size", "7", "--cursor", cursor, "--json")
    second = json.loads(out)
    assert len(second["rows"]) == 7
    with Store(db) as store:
        expected = store.ordered_ids(Query())
    assert [row["id"] for row in second["rows"]] == expected[7:14]


def test_scan_is_a_gate_that_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = seed(tmp_path)
    status, out, _ = run(capsys, "--db", str(db), "scan", "--size", "7")
    assert status == 0
    assert "0 duplicate(s), 0 missing" in out


def test_scan_counts_in_cursor_order(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = seed(tmp_path)
    _, out, _ = run(capsys, "--db", str(db), "scan", "--size", "7", "--order", "title")
    with Store(db) as store:
        expected = store.ordered_ids(Query(Order("title")))
    printed = [int(value) for value in out.splitlines()[0].split()]
    assert printed == expected


def test_demo_proves_the_contrast(capsys: pytest.CaptureFixture[str]) -> None:
    """Exit 0 means the demonstration still holds: cursors clean, OFFSET still losing rows.

    A non-zero exit is the interesting case — it means either a cursor walk lost a
    row or OFFSET stopped being broken, and in both cases the demo is no longer
    evidence of anything.
    """
    status, out, _ = run(capsys, "demo")
    assert status == 0
    assert "cursor clean" in out
    assert "offset: skipped 1" in out
    assert "0 offset walk(s) that survived" in out
    assert "2 scenarios" in out


def test_a_cursor_from_another_query_exits_two(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = seed(tmp_path)
    _, out, _ = run(capsys, "--db", str(db), "page", "--size", "7", "--json")
    cursor = json.loads(out)["next_cursor"]
    status, _, err = run(capsys, "--db", str(db), "page", "--cursor", cursor, "--order", "title")
    assert status == 2
    assert "different query" in err


def test_a_bad_size_exits_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db = seed(tmp_path)
    status, _, err = run(capsys, "--db", str(db), "page", "--size", "0")
    assert status == 2
    assert "at least 1" in err


def test_a_missing_database_is_created_not_refused(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db = tmp_path / "new.db"
    status, out, _ = run(capsys, "--db", str(db), "page")
    assert status == 0
    assert "0 row(s)" in out
    assert db.exists()


def test_version_is_available() -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main(["--version"])
    assert caught.value.code == 0
