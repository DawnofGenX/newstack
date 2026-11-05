"""The CLI is the interface an auditor uses: append, list, verify, checkpoint."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject


@pytest.fixture
def db(tmp_path: Path) -> str:
    return str(tmp_path / "audit.db")


def run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    status = subject.main(list(argv))
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def test_append_prints_the_sequence_and_hash(capsys: pytest.CaptureFixture[str], db: str) -> None:
    argv = ("--db", db, "append", "--actor", "alice", "--action", "note.update", "--target", "n/1")
    status, out, _ = run(capsys, *argv)
    assert status == 0
    assert out.startswith("seq 1  hash ")
    assert "actor   alice" in out


def test_details_stay_strings_unless_json_says_otherwise(
    capsys: pytest.CaptureFixture[str], db: str
) -> None:
    base = ("--db", db, "append", "--actor", "a", "--action", "x", "--target", "t")
    run(capsys, *base, "--detail", "attempts=3", "--detail-json", '{"ratio": "0.5"}')
    status, out, _ = run(capsys, "--db", db, "list", "--json")
    payload = json.loads(out)[0]
    assert status == 0
    assert payload["detail"] == {"attempts": "3", "ratio": "0.5"}
    assert payload["detail"]["attempts"] != 3


def test_verify_reports_a_clean_log(capsys: pytest.CaptureFixture[str], db: str) -> None:
    run(capsys, "--db", db, "append", "--actor", "a", "--action", "x", "--target", "t")
    status, out, _ = run(capsys, "--db", db, "verify")
    assert status == 0
    assert out.startswith("verify  ok: 1 event(s)")


def test_verify_exits_one_when_a_row_was_edited(
    capsys: pytest.CaptureFixture[str], db: str
) -> None:
    run(capsys, "--db", db, "append", "--actor", "alice", "--action", "x", "--target", "t")
    import sqlite3

    connection = sqlite3.connect(db)
    connection.execute("UPDATE events SET body = replace(body, 'alice', 'mallory') WHERE seq = 1")
    connection.commit()
    connection.close()
    status, out, _ = run(capsys, "--db", db, "verify")
    assert status == 1
    assert "verify  FAILED" in out
    assert "body-changed" in out


def test_a_checkpoint_catches_a_rewrite(capsys: pytest.CaptureFixture[str], db: str) -> None:
    for index in range(1, 4):
        run(capsys, "--db", db, "append", "--actor", "a", "--action", "x", "--target", f"t/{index}")
    head = Path(db).with_name("head.json")
    status, out, _ = run(capsys, "--db", db, "checkpoint", "--out", str(head))
    assert status == 0
    assert "checkpoint  seq 3" in out

    from {{ package_name }} import demo as demo_mod
    from {{ package_name }} import store as store_mod

    store = store_mod.Store(Path(db))
    demo_mod.rebuild_chain(store)
    store.close()
    status, out, _ = run(capsys, "--db", db, "verify")
    assert status == 0
    status, out, _ = run(capsys, "--db", db, "verify", "--checkpoint", str(head))
    assert status == 1
    assert "rewritten" in out


def test_a_bad_detail_exits_two(capsys: pytest.CaptureFixture[str], db: str) -> None:
    base = ("--db", db, "append", "--actor", "a", "--action", "x", "--target", "t")
    status, _, err = run(capsys, *base, "--detail", "novalue")
    assert status == 2
    assert "key=value" in err


def test_a_duplicate_detail_exits_two(capsys: pytest.CaptureFixture[str], db: str) -> None:
    base = ("--db", db, "append", "--actor", "a", "--action", "x", "--target", "t")
    status, _, err = run(capsys, *base, "--detail", "a=1", "--detail", "a=2")
    assert status == 2
    assert "twice" in err


def test_a_float_in_detail_json_exits_two(capsys: pytest.CaptureFixture[str], db: str) -> None:
    base = ("--db", db, "append", "--actor", "a", "--action", "x", "--target", "t")
    status, _, err = run(capsys, *base, "--detail-json", '{"ratio": 0.5}')
    assert status == 2
    assert "is a float" in err


def test_list_prints_one_row_per_event(capsys: pytest.CaptureFixture[str], db: str) -> None:
    for index in range(1, 3):
        run(capsys, "--db", db, "append", "--actor", "a", "--action", "x", "--target", f"t/{index}")
    status, out, _ = run(capsys, "--db", db, "list")
    rows = [line for line in out.splitlines() if "T" in line and line.strip()[0].isdigit()]
    lines = rows
    assert status == 0
    assert len(lines) == 2
    assert "2 event(s) listed; 2 in the log" in out


def test_demo_proves_all_three_attacks(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "demo")
    assert status == 1  # the chain-only rewrite is deliberately missed, so the demo fails loudly
    assert out.count("caught") == 4
    assert out.count("MISSED") == 1
    assert "demo: 5 scenarios, 1 missed" in out


def test_selftest_passes(capsys: pytest.CaptureFixture[str]) -> None:
    status, out, _ = run(capsys, "selftest")
    assert status == 0
    assert "0 failed" in out


def test_version_is_available() -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main(["--version"])
    assert caught.value.code == 0
