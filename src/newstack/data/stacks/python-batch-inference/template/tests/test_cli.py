"""End-to-end through the real CLI against the stub server."""

from __future__ import annotations

import io
import json

import pytest

from {{ package_name }} import cli

from .stub import serve

REQUESTS = [
    {"id": "cap-1", "prompt": "Say hello"},
    {"id": "flaky-3", "prompt": "FAIL429 retry me"},
]


@pytest.fixture
def stub():
    server, _state = serve(flaky_after=1)
    yield f"http://127.0.0.1:{server.server_address[1]}/v1"
    server.shutdown()
    server.server_close()


def write(path, rows) -> str:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    return str(path)


def test_a_clean_batch_exits_zero_and_writes_one_line_per_request(tmp_path, stub, capsys) -> None:
    requests = write(tmp_path / "requests.jsonl", REQUESTS)
    out = tmp_path / "results.jsonl"
    code = cli.main(["run", "--requests", requests, "--out", str(out), "--base-url", stub])
    assert code == 0
    assert "ok        2" in capsys.readouterr().out
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert [row["id"] for row in rows] == ["cap-1", "flaky-3"]
    assert rows[1]["attempts"] == 2, "the 429 was retried, not hidden"
    assert rows[0]["output"] == "echo: Say hello"


def test_a_permanent_failure_exits_one_but_keeps_the_answers(tmp_path, stub, capsys) -> None:
    rows = [*REQUESTS, {"id": "bad-4", "prompt": "FAIL400 doomed"}]
    requests = write(tmp_path / "requests.jsonl", rows)
    out = tmp_path / "results.jsonl"
    code = cli.main(["run", "--requests", requests, "--out", str(out), "--base-url", stub])
    assert code == 1
    printed = capsys.readouterr().out
    assert "failed    1" in printed
    assert "failure   bad-4: http 400" in printed
    saved = [json.loads(line) for line in out.read_text().splitlines()]
    assert len(saved) == 3
    assert {row["id"] for row in saved if row["ok"]} == {"cap-1", "flaky-3"}


def test_a_rerun_skips_ids_already_in_the_results_file(tmp_path, stub, capsys) -> None:
    requests = write(tmp_path / "requests.jsonl", REQUESTS)
    out = tmp_path / "results.jsonl"
    assert cli.main(["run", "--requests", requests, "--out", str(out), "--base-url", stub]) == 0
    first = out.read_text()
    capsys.readouterr()
    assert cli.main(["run", "--requests", requests, "--out", str(out), "--base-url", stub]) == 0
    assert "resumed   2" in capsys.readouterr().out
    assert out.read_text() == first, "a resumed run writes nothing new"


def test_no_resume_sends_everything_again(tmp_path, stub, capsys) -> None:
    requests = write(tmp_path / "requests.jsonl", REQUESTS)
    out = tmp_path / "results.jsonl"
    cli.main(["run", "--requests", requests, "--out", str(out), "--base-url", stub])
    cli.main(["run", "--requests", requests, "--out", str(out), "--base-url", stub, "--no-resume"])
    assert "resumed   0" in capsys.readouterr().out
    assert len(out.read_text().splitlines()) == 4


def test_limit_sends_only_the_first_pending_requests(tmp_path, stub, capsys) -> None:
    requests = write(tmp_path / "requests.jsonl", REQUESTS)
    out = tmp_path / "results.jsonl"
    code = cli.main(
        ["run", "--requests", requests, "--out", str(out), "--base-url", stub, "--limit", "1"]
    )
    assert code == 0
    assert "ok        1" in capsys.readouterr().out
    assert len(out.read_text().splitlines()) == 1


def test_requests_can_come_from_stdin(tmp_path, stub, capsys, monkeypatch) -> None:
    body = "".join(json.dumps(row) + "\n" for row in REQUESTS)
    monkeypatch.setattr("sys.stdin", io.StringIO(body))
    out = tmp_path / "results.jsonl"
    assert cli.main(["run", "--requests", "-", "--out", str(out), "--base-url", stub]) == 0
    assert len(out.read_text().splitlines()) == 2


def test_a_missing_requests_file_exits_two(tmp_path, capsys) -> None:
    code = cli.main(["run", "--requests", str(tmp_path / "nope.jsonl"), "--out", "x.jsonl"])
    assert code == 2
    assert "cannot read" in capsys.readouterr().err


def test_a_duplicate_id_exits_two_and_writes_nothing(tmp_path, capsys) -> None:
    requests = write(tmp_path / "requests.jsonl", [REQUESTS[0], REQUESTS[0]])
    out = tmp_path / "results.jsonl"
    code = cli.main(["run", "--requests", requests, "--out", str(out), "--base-url", stub_url()])
    assert code == 2
    assert "duplicate id" in capsys.readouterr().err
    assert not out.exists()


def stub_url() -> str:
    """A URL nothing listens on: this test must fail before any request is sent."""
    return "http://127.0.0.1:9/v1"


def test_the_version_flag_prints_the_package_version(capsys) -> None:
    with pytest.raises(SystemExit) as caught:
        cli.main(["--version"])
    assert caught.value.code == 0
    assert "0.1.0" in capsys.readouterr().out
