"""The command line, including the exit codes a script would depend on."""

import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject


def quiet(monkeypatch):
    """Capture console output without touching the streams the test reporter uses."""
    printed: list[str] = []
    def collect(*parts, **kwargs) -> None:
        del kwargs
        printed.append(" ".join(str(part) for part in parts))

    monkeypatch.setattr("builtins.print", collect)
    return printed


def test_simulate_exits_zero(monkeypatch):
    printed = quiet(monkeypatch)
    assert subject.main(["simulate", "--accesses", "400"]) == 0
    assert any("ceiling" in line for line in printed)


def test_simulate_reports_the_policy_it_ran(monkeypatch):
    printed = quiet(monkeypatch)
    subject.main(["simulate", "--policy", "fifo", "--accesses", "400"])
    assert any(line.startswith("fifo") for line in printed)


def test_a_missed_threshold_exits_one(monkeypatch):
    printed = quiet(monkeypatch)
    code = subject.main(["simulate", "--accesses", "400", "--min-hit-rate", "0.99"])
    assert code == 1
    assert any("BREACH" in line for line in printed)


def test_a_met_threshold_exits_zero(monkeypatch):
    quiet(monkeypatch)
    assert subject.main(["simulate", "--accesses", "400", "--min-hit-rate", "0.0"]) == 0


def test_compare_names_a_best_policy(monkeypatch):
    printed = quiet(monkeypatch)
    assert subject.main(["compare", "--accesses", "800"]) == 0
    assert any(line.startswith("best") for line in printed)


def test_curve_prints_every_capacity(monkeypatch):
    printed = quiet(monkeypatch)
    assert subject.main(["curve", "--capacities", "5,25", "--accesses", "400"]) == 0
    rows = [line for line in printed if line.strip()[:1] == "5" or line.strip()[:2] == "25"]
    assert any(line.startswith("       5") for line in rows)
    assert any(line.startswith("      25") for line in rows)


def test_json_output_is_parseable(monkeypatch, capsys):
    subject.main(["simulate", "--accesses", "300", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["accesses"] == 300
    assert "ceiling" in payload
    assert payload["policy"] == "lru"


def test_compare_json_carries_every_policy(capsys):
    subject.main(["compare", "--accesses", "300", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert [row["policy"] for row in payload["results"]] == list(subject.POLICIES)


def test_an_unknown_trace_is_an_argparse_error():
    with pytest.raises(SystemExit) as raised:
        subject.main(["simulate", "--trace", "spiral"])
    assert raised.value.code == 2


def test_unreadable_capacities_exit_two():
    with pytest.raises(SystemExit) as raised:
        subject.main(["curve", "--capacities", "ten"])
    assert raised.value.code == 2


def test_a_zero_capacity_is_unusable():
    assert subject.main(["simulate", "--capacity", "0"]) == subject.EXIT_UNUSABLE


def test_the_demo_holds(capsys):
    assert subject.main(["demo"]) == 0
    assert "demo" not in capsys.readouterr().out.splitlines()[0]


def test_selftest_reports_its_checks(capsys):
    assert subject.main(["selftest"]) == 0
    assert "checks passed" in capsys.readouterr().out


def test_the_version_flag_prints_a_version(capsys):
    with pytest.raises(SystemExit) as raised:
        subject.main(["--version"])
    assert raised.value.code == 0
    assert subject.VERSION in capsys.readouterr().out


def test_the_program_name_is_the_command(monkeypatch):
    assert subject.PROGRAM


def test_no_command_is_an_error():
    with pytest.raises(SystemExit) as raised:
        subject.main([])
    assert raised.value.code == 2


def test_an_unknown_command_is_an_error():
    with pytest.raises(SystemExit) as raised:
        subject.main(["polish"])
    assert raised.value.code == 2


def test_the_json_writer_does_not_need_a_path(monkeypatch, tmp_path: Path):
    quiet(monkeypatch)
    assert subject.main(["curve", "--capacities", "5", "--accesses", "200"]) == 0
    assert not list(tmp_path.iterdir())
