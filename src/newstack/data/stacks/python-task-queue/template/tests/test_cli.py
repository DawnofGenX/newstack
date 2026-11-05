"""The console script: exit codes a shell can branch on."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject


@pytest.fixture
def database(tmp_path: Path) -> str:
    return str(tmp_path / "queue.db")


def run(database: str, *args: str) -> int:
    return subject.main(["--db", database, *args])


def test_push_then_claim_then_complete(database: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(database, "push", '{"task": "resize"}') == subject.EXIT_OK
    job_id = capsys.readouterr().out.strip()
    assert len(job_id) == 32

    assert run(database, "claim", "--worker", "w1") == subject.EXIT_OK
    job = json.loads(capsys.readouterr().out)
    assert job["id"] == job_id
    assert job["attempts"] == 1

    assert run(database, "complete", job_id, "--worker", "w1") == subject.EXIT_OK
    assert run(database, "stats") == subject.EXIT_OK
    assert "done=1" in capsys.readouterr().out


def test_claiming_an_empty_queue_exits_one(
    database: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run(database, "claim") == subject.EXIT_NOTHING
    assert "nothing to claim" in capsys.readouterr().err


def test_a_bad_payload_exits_two(database: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(database, "push", "not json") == subject.EXIT_UNUSABLE
    assert "not JSON" in capsys.readouterr().err
    assert run(database, "push", "[1, 2]") == subject.EXIT_UNUSABLE
    assert "must be a JSON object" in capsys.readouterr().err


def test_a_payload_can_come_from_a_file(
    database: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "payload.json"
    path.write_text('{"from": "file"}')
    assert run(database, "push", f"@{path}") == subject.EXIT_OK
    job_id = capsys.readouterr().out.strip()
    assert run(database, "list", "--json") == subject.EXIT_OK
    assert json.loads(capsys.readouterr().out)[0]["payload"] == {"from": "file"}
    assert run(database, "list") == subject.EXIT_OK
    assert job_id[:12] in capsys.readouterr().out


def test_completing_someone_elses_lease_exits_two(
    database: str, capsys: pytest.CaptureFixture[str]
) -> None:
    run(database, "push", '{"n": 1}')
    job_id = capsys.readouterr().out.strip()
    run(database, "claim", "--worker", "w1")
    capsys.readouterr()
    assert run(database, "complete", job_id, "--worker", "w2") == subject.EXIT_UNUSABLE
    assert "not leased by w2" in capsys.readouterr().err


def test_a_dead_letter_is_reported_by_exit_code(
    database: str, capsys: pytest.CaptureFixture[str]
) -> None:
    run(database, "push", '{"n": 1}', "--max-attempts", "1")
    job_id = capsys.readouterr().out.strip()
    run(database, "claim", "--worker", "w1")
    capsys.readouterr()
    assert (
        run(database, "fail", job_id, "--worker", "w1", "--error", "boom") == subject.EXIT_NOTHING
    )
    assert capsys.readouterr().out.strip() == "dead"
    assert run(database, "list", "--state", "dead") == subject.EXIT_OK
    assert job_id[:12] in capsys.readouterr().out


def test_drain_prints_a_summary(database: str, capsys: pytest.CaptureFixture[str]) -> None:
    for n in range(2):
        run(database, "push", json.dumps({"n": n}))
    capsys.readouterr()
    assert run(database, "drain") == subject.EXIT_OK
    assert "drained 2 done" in capsys.readouterr().out
    assert run(database, "drain", "--json") == subject.EXIT_OK
    assert json.loads(capsys.readouterr().out)["claimed"] == 0


def test_list_refuses_an_unknown_state(database: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(database, "list", "--state", "sold") == subject.EXIT_UNUSABLE
    assert "unknown state" in capsys.readouterr().err


def test_the_selftest_passes(capsys: pytest.CaptureFixture[str]) -> None:
    assert subject.main(["selftest"]) == subject.EXIT_OK
    assert "checks passed" in capsys.readouterr().out


def test_a_handler_must_be_importable(database: str, capsys: pytest.CaptureFixture[str]) -> None:
    assert run(database, "drain", "--handler", "no.such.module:work") == subject.EXIT_UNUSABLE
    assert "cannot import" in capsys.readouterr().err
    assert run(database, "drain", "--handler", "nothing") == subject.EXIT_UNUSABLE
    assert "module:function" in capsys.readouterr().err
