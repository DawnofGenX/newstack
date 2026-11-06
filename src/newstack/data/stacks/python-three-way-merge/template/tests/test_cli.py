from __future__ import annotations

import json
from pathlib import Path

import pytest

from {{ package_name }} import cli as subject

BASE = "a\nb\nc\n"


def fixtures(tmp_path: Path) -> tuple[Path, Path, Path]:
    base = tmp_path / "base.txt"
    ours = tmp_path / "ours.txt"
    theirs = tmp_path / "theirs.txt"
    base.write_text(BASE, encoding="utf-8")
    ours.write_text("a\nB\nc\n", encoding="utf-8")
    theirs.write_text("a\nb\nC\n", encoding="utf-8")
    return base, ours, theirs


def run(tmp_path: Path, *extra: str) -> int:
    base, ours, theirs = fixtures(tmp_path)
    return subject.main(
        ["merge", "--base", str(base), "--ours", str(ours), "--theirs", str(theirs), *extra]
    )


def test_a_clean_merge_exits_zero(tmp_path, capsys) -> None:
    assert run(tmp_path) == 0
    out = capsys.readouterr().out
    assert out == "a\nB\nC\n"


def test_a_conflict_exits_one_and_writes_markers(tmp_path, capsys) -> None:
    base, ours, theirs = fixtures(tmp_path)
    theirs.write_text("a\nZ\nc\n", encoding="utf-8")
    code = subject.main(
        ["merge", "--base", str(base), "--ours", str(ours), "--theirs", str(theirs)]
    )
    assert code == 1
    assert "<<<<<<< ours" in capsys.readouterr().out


def test_json_reports_the_verdict(tmp_path, capsys) -> None:
    base, ours, theirs = fixtures(tmp_path)
    theirs.write_text("a\nZ\nc\n", encoding="utf-8")
    code = subject.main(
        ["merge", "--base", str(base), "--ours", str(ours), "--theirs", str(theirs), "--json"]
    )
    assert code == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["clean"] is False
    assert payload["conflicts"] == 1
    assert payload["changes"] == {"ours": 1, "theirs": 1}


def test_out_writes_the_file_and_keeps_stdout_empty(tmp_path, capsys) -> None:
    out = tmp_path / "merged.txt"
    assert run(tmp_path, "--out", str(out)) == 0
    assert capsys.readouterr().out == ""
    assert out.read_text(encoding="utf-8") == "a\nB\nC\n"


def test_labels_reach_the_markers(tmp_path, capsys) -> None:
    base, ours, theirs = fixtures(tmp_path)
    theirs.write_text("a\nZ\nc\n", encoding="utf-8")
    code = subject.main(
        [
            "merge",
            "--base",
            str(base),
            "--ours",
            str(ours),
            "--theirs",
            str(theirs),
            "--labels",
            "mine,yours",
        ]
    )
    assert code == 1
    out = capsys.readouterr().out
    assert "<<<<<<< mine" in out and ">>>>>>> yours" in out


def test_diff3_adds_the_base_section(tmp_path, capsys) -> None:
    base, ours, theirs = fixtures(tmp_path)
    theirs.write_text("a\nZ\nc\n", encoding="utf-8")
    subject.main(
        [
            "merge",
            "--base",
            str(base),
            "--ours",
            str(ours),
            "--theirs",
            str(theirs),
            "--style",
            "diff3",
        ]
    )
    assert "||||||| base" in capsys.readouterr().out


def test_a_missing_file_is_unusable(tmp_path) -> None:
    base, ours, _ = fixtures(tmp_path)
    assert (
        subject.main(
            [
                "merge",
                "--base",
                str(base),
                "--ours",
                str(ours),
                "--theirs",
                str(tmp_path / "nope.txt"),
            ]
        )
        == 2
    )


def test_one_label_is_unusable(tmp_path, capsys) -> None:
    assert run(tmp_path, "--labels", "ours") == 2
    assert "two names" in capsys.readouterr().err


def test_an_unknown_style_is_unusable(tmp_path) -> None:
    with pytest.raises(SystemExit) as caught:
        run(tmp_path, "--style", "squash")
    assert caught.value.code == 2


def test_explain_prints_the_chunks(tmp_path, capsys) -> None:
    base, ours, theirs = fixtures(tmp_path)
    code = subject.main(
        ["explain", "--base", str(base), "--ours", str(ours), "--theirs", str(theirs)]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert out.startswith("merge      chunks")
    assert " 2  ours" in out


def test_version_names_the_program(capsys) -> None:
    with pytest.raises(SystemExit) as caught:
        subject.main(["--version"])
    assert caught.value.code == 0
    assert capsys.readouterr().out.startswith(f"{subject.PROGRAM} ")


def test_help_lists_merge(capsys) -> None:
    with pytest.raises(SystemExit):
        subject.main(["--help"])
    assert "merge" in capsys.readouterr().out


def test_demo_holds_every_story(capsys) -> None:
    assert subject.main(["demo"]) == 0
    assert "stories      6 of 6 hold" in capsys.readouterr().out
