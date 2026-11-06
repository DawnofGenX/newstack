"""The command line: exit codes, JSON payloads, and error handling."""

from __future__ import annotations

import json

import pytest

from {{ package_name }} import cli as subject


@pytest.fixture()
def project(tmp_path):
    ignore = tmp_path / ".gitignore"
    ignore.write_text("*.log\nbuild/\n!keep.log\n", encoding="utf-8")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "out.js").write_text("x", encoding="utf-8")
    (tmp_path / "app.log").write_text("x", encoding="utf-8")
    (tmp_path / "main.py").write_text("x", encoding="utf-8")
    return tmp_path, ignore


def test_an_ignored_path_exits_one(project, capsys) -> None:
    _, ignore = project
    status = subject.main(["explain", "app.log", "--ignore", str(ignore)])
    assert status == subject.EXIT_IGNORED
    out = capsys.readouterr().out
    assert "verdict    ignored" in out
    assert "line 1: *.log" in out


def test_a_tracked_path_exits_zero(project, capsys) -> None:
    _, ignore = project
    assert subject.main(["explain", "main.py", "--ignore", str(ignore)]) == subject.EXIT_OK
    assert "verdict    not ignored" in capsys.readouterr().out


def test_a_negated_rule_is_reported_as_the_decider(project, capsys) -> None:
    _, ignore = project
    subject.main(["explain", "keep.log", "--ignore", str(ignore), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["ignored"] is False
    assert payload["rule"] == "!keep.log"
    assert payload["line"] == 3


def test_explain_can_treat_a_path_as_a_directory(project, capsys) -> None:
    _, ignore = project
    subject.main(["explain", "build", "--ignore", str(ignore), "--directory", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["is_dir"] is True
    assert payload["ignored"] is True


def test_list_reports_every_rule_with_its_flags(project, capsys) -> None:
    _, ignore = project
    assert subject.main(["list", "--ignore", str(ignore), "--json"]) == subject.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert [entry["line"] for entry in payload] == [1, 2, 3]
    assert payload[1]["dir_only"] is True
    assert payload[2]["negated"] is True


def test_walk_counts_what_it_finds(project, capsys) -> None:
    root, ignore = project
    subject.main(["walk", str(root), "--ignore", str(ignore), "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["paths"] == 5
    assert payload["ignored"] == 3
    assert sorted(entry["path"] for entry in payload["entries"]) == [
        "app.log",
        "build",
        "build/out.js",
    ]


def test_walk_can_show_tracked_paths_too(project, capsys) -> None:
    root, ignore = project
    subject.main(["walk", str(root), "--ignore", str(ignore), "--json", "--all"])
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["entries"]) == 5


def test_a_missing_ignore_file_is_unusable(project, capsys) -> None:
    root, _ = project
    status = subject.main(["explain", "a.log", "--ignore", str(root / "absent")])
    assert status == subject.EXIT_UNUSABLE
    assert "no such ignore file" in capsys.readouterr().err


def test_a_path_that_escapes_the_tree_is_unusable(project, capsys) -> None:
    _, ignore = project
    status = subject.main(["explain", "../outside", "--ignore", str(ignore)])
    assert status == subject.EXIT_UNUSABLE
    assert "steps outside the tree" in capsys.readouterr().err


def test_selftest_and_demo_are_routed(project) -> None:
    parser = subject.build_parser()
    assert parser.parse_args(["selftest"]).handler is subject._command_selftest
    assert parser.parse_args(["demo"]).handler is subject._command_demo


def test_the_version_is_printed(capsys) -> None:
    with pytest.raises(SystemExit):
        subject.main(["--version"])
    assert subject.VERSION in capsys.readouterr().out
