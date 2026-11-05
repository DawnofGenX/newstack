import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject


def run(tmp_path: Path, *argv: str, capsys):
    code = subject.main(["--db", str(tmp_path / "cli.db"), *argv])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_place_and_show(tmp_path: Path, capsys) -> None:
    code, out, _ = run(tmp_path, "place", "--amount", "1200", capsys=capsys)
    assert code == 0
    assert "placed  order 1 for 1200" in out
    assert "pending: 1" in out
    code, out, _ = run(tmp_path, "show", capsys=capsys)
    assert code == 0
    assert "order    1      1200  placed" in out
    assert "1 order(s), 1 event(s) shown, 1 pending" in out


def test_relay_publishes_and_marks(tmp_path: Path, capsys) -> None:
    run(tmp_path, "place", "--amount", "100", capsys=capsys)
    code, out, _ = run(tmp_path, "relay", capsys=capsys)
    assert code == 0
    assert "publish " in out
    assert "relay   delivered 1, blocked 0" in out
    code, out, _ = run(tmp_path, "show", "--pending", capsys=capsys)
    assert code == 0
    assert "0 pending" in out
    assert "order    1       100  placed" in out


def test_a_crash_exits_one_and_leaves_work(tmp_path: Path, capsys) -> None:
    run(tmp_path, "place", "--amount", "100", capsys=capsys)
    run(tmp_path, "place", "--amount", "200", capsys=capsys)
    code, out, err = run(tmp_path, "relay", "--crash-after", "1", capsys=capsys)
    assert code == 1
    assert "relay   delivered 0, blocked 0, crashed before marking" in out
    assert "died after the sink accepted it" in err
    code, out, _ = run(tmp_path, "show", "--pending", capsys=capsys)
    assert "2 pending" in out


def test_the_event_json_is_an_envelope(tmp_path: Path, capsys) -> None:
    run(tmp_path, "place", "--amount", "100", capsys=capsys)
    _, out, _ = run(tmp_path, "relay", capsys=capsys)
    line = next(row for row in out.splitlines() if row.startswith("publish "))
    envelope = json.loads(line.split(" ", 5)[5])
    assert envelope["version"] == 1
    assert envelope["aggregate"] == "order:1"
    assert envelope["payload"] == {"amount": 100, "order": 1}


def test_pay_twice_exits_two(tmp_path: Path, capsys) -> None:
    run(tmp_path, "place", "--amount", "100", capsys=capsys)
    assert run(tmp_path, "pay", "1", capsys=capsys)[0] == 0
    code, _, err = run(tmp_path, "pay", "1", capsys=capsys)
    assert code == 2
    assert "already paid" in err


def test_a_bad_amount_exits_two(tmp_path: Path, capsys) -> None:
    code, _, err = run(tmp_path, "place", "--amount", "0", capsys=capsys)
    assert code == 2
    assert "amount must be positive" in err


def test_demo_exits_zero(tmp_path: Path, capsys) -> None:
    code, out, _ = run(tmp_path, "demo", capsys=capsys)
    assert code == 0
    assert "exactly once" in out
    assert "demo: 3 scenarios, 0 not as advertised" in out


def test_selftest_exits_zero(tmp_path: Path, capsys) -> None:
    code, out, _ = run(tmp_path, "selftest", capsys=capsys)
    assert code == 0
    assert "0 failed" in out


def test_no_command_is_a_usage_error(capsys) -> None:
    with pytest.raises(SystemExit):
        subject.main([])


def test_version_is_a_system_exit(capsys) -> None:
    with pytest.raises(SystemExit):
        subject.main(["--version"])
