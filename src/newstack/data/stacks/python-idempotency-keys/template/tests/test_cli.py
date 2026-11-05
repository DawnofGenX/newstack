import json

import pytest

from {{ package_name }} import cli as cli_mod

KEY = "order-8f3a1c2d"


def run(capsys, *argv: str) -> tuple[int, str, str]:
    status = cli_mod.main(list(argv))
    captured = capsys.readouterr()
    return status, captured.out, captured.err


def test_the_first_request_executes(tmp_path, capsys) -> None:
    status, out, err = run(capsys, "--db", str(tmp_path / "k.db"), "request", "--key", KEY)
    assert (status, err) == (0, "")
    assert "execute" in out
    assert "status 201" in out


def test_the_second_request_replays(tmp_path, capsys) -> None:
    db = str(tmp_path / "k.db")
    run(capsys, "--db", db, "request", "--key", KEY)
    status, out, err = run(capsys, "--db", db, "request", "--key", KEY)
    assert (status, err) == (0, "")
    assert "replay" in out


def test_the_json_flag_carries_the_replay_marker(tmp_path, capsys) -> None:
    db = str(tmp_path / "k.db")
    run(capsys, "--db", db, "request", "--key", KEY)
    status, out, err = run(capsys, "--db", db, "request", "--key", KEY, "--json")
    payload = json.loads(out)
    assert status == 0
    assert err == ""
    assert payload["replay"] is True
    assert payload["status"] == 201


def test_a_different_body_is_refused(tmp_path, capsys) -> None:
    db = str(tmp_path / "k.db")
    run(capsys, "--db", db, "request", "--key", KEY, "--body", '{"amount": 1200}')
    status, out, err = run(capsys, "--db", db, "request", "--key", KEY, "--body", '{"amount": 5}')
    assert status == 1
    assert out == ""
    assert "mismatch" in err


def test_show_prints_the_row(tmp_path, capsys) -> None:
    db = str(tmp_path / "k.db")
    run(capsys, "--db", db, "request", "--key", KEY)
    status, out, err = run(capsys, "--db", db, "show", "--key", KEY)
    assert (status, err) == (0, "")
    assert "fingerprint" in out
    assert "completed" in out


def test_show_on_an_unknown_key_exits_two(tmp_path, capsys) -> None:
    status, out, err = run(capsys, "--db", str(tmp_path / "k.db"), "show", "--key", KEY)
    assert status == 2
    assert out == ""
    assert "no key" in err


def test_a_body_that_is_not_json_exits_two(tmp_path, capsys) -> None:
    status, out, err = run(capsys, "--db", str(tmp_path / "k.db"), "request", "--key", KEY,
                           "--body", "{oops")
    assert status == 2
    assert out == ""
    assert "not JSON" in err


def test_a_body_that_is_not_an_object_exits_two(tmp_path, capsys) -> None:
    status, _out, err = run(capsys, "--db", str(tmp_path / "k.db"), "request", "--key", KEY,
                            "--body", "[1, 2]")
    assert status == 2
    assert "JSON object" in err


def test_a_failing_handler_exits_two_and_releases_the_key(tmp_path, capsys) -> None:
    db = str(tmp_path / "k.db")
    status, out, err = run(capsys, "--db", db, "request", "--key", KEY, "--handler", "fail")
    assert status == 2
    assert "provider refused" in err
    status, out, err = run(capsys, "--db", db, "request", "--key", KEY)
    assert status == 0
    assert "attempts 2" in out


def test_an_unknown_handler_is_a_usage_error(tmp_path) -> None:
    with pytest.raises(SystemExit):
        cli_mod.main(["--db", str(tmp_path / "k.db"), "request", "--key", KEY,
                      "--handler", "melt"])


def test_the_demo_exits_zero(tmp_path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    status, out, err = run(capsys, "demo")
    assert (status, err) == (0, "")
    assert "0 not as advertised" in out


def test_the_selftest_reports_no_failures(capsys) -> None:
    status, out, err = run(capsys, "selftest")
    assert status == 0
    assert err == ""
    assert "0 failed" in out


def test_version_exits_zero() -> None:
    with pytest.raises(SystemExit) as caught:
        cli_mod.main(["--version"])
    assert caught.value.code == 0
