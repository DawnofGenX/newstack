from __future__ import annotations

import json

from {{ package_name }} import cli, journal


def test_a_clean_run_exits_zero(tmp_path):
    code = cli.main(["run", "--journal", str(tmp_path / "j.jsonl"), "--decline", ""])
    assert code == cli.EXIT_COMPLETED


def test_a_declined_run_exits_one_and_compensates(tmp_path):
    path = tmp_path / "j.jsonl"
    code = cli.main(["run", "--journal", str(path)])
    assert code == cli.EXIT_ROLLED_BACK
    statuses = journal.Journal(path).statuses("book-trip")
    assert statuses["charge-card"] == "compensated"
    assert statuses["book-flight"] == "failed"


def test_a_broken_compensation_exits_two(tmp_path):
    code = cli.main(
        ["run", "--journal", str(tmp_path / "j.jsonl"), "--break-compensation", "charge-card"]
    )
    assert code == cli.EXIT_INCOMPLETE


def test_json_output_describes_the_outcome(tmp_path):
    path = tmp_path / "j.jsonl"
    code = cli.main(["run", "--journal", str(path), "--json"])
    assert code == cli.EXIT_ROLLED_BACK


def test_the_journal_command_reads_back_what_the_run_wrote(tmp_path, capsys):
    path = tmp_path / "j.jsonl"
    cli.main(["run", "--journal", str(path)])
    capsys.readouterr()
    code = cli.main(["journal", "--journal", str(path), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert code == cli.EXIT_ROLLED_BACK
    assert payload["outcome"] == "rolled_back"
    assert payload["steps"]["book-flight"] == "failed"


def test_an_empty_journal_is_unusable_input(tmp_path):
    code = cli.main(["journal", "--journal", str(tmp_path / "missing.jsonl")])
    assert code == cli.EXIT_UNUSABLE


def test_the_demo_reports_its_worst_scenario(capsys):
    assert cli.main(["demo"]) == cli.EXIT_INCOMPLETE
    output = capsys.readouterr().out
    assert "the refund endpoint is down" in output
    assert "status     rolled_back" in output


def test_no_command_prints_help_and_exits_three(capsys):
    assert cli.main([]) == cli.EXIT_UNUSABLE
    assert "usage" in capsys.readouterr().out.lower()


def test_selftest_passes(capsys):
    assert cli.main(["selftest"]) == 0
    assert "checks passed" in capsys.readouterr().out


def test_a_broken_journal_is_reported_not_raised(tmp_path, capsys):
    path = tmp_path / "bad.jsonl"
    path.write_text(
        '{"seq": 1, "event": "saga.started", "saga": "s"}\n{"se\n'
        '{"seq": 3, "event": "saga.completed", "saga": "s"}\n'
    )
    assert cli.main(["journal", "--journal", str(path)]) == cli.EXIT_UNUSABLE
    assert "error:" in capsys.readouterr().err
