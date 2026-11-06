from __future__ import annotations

from pathlib import Path

import pytest

from {{ package_name }} import cli

TEXT = "alpha bravo charlie\n(delta echo)"


@pytest.fixture()
def source(tmp_path: Path) -> Path:
    path = tmp_path / "text.txt"
    path.write_text(TEXT, encoding="utf-8")
    return path


def run(*argv: str) -> int:
    return cli.main(list(argv))


def test_version_and_help_exit_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert run("--version") == 0
    assert run("--help") == 0
    printed = capsys.readouterr().out
    assert "selftest" in printed


def test_load_shows_the_spine(capsys: pytest.CaptureFixture[str], source: Path) -> None:
    assert run("load", "--text", str(source)) == 0
    printed = capsys.readouterr().out
    assert "balanced   True" in printed
    assert TEXT in printed


def test_load_json_names_the_chunks(capsys: pytest.CaptureFixture[str], source: Path) -> None:
    import json

    assert run("load", "--text", str(source), "--json") == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["size"] == len(TEXT)
    assert payload["text"] == TEXT


def test_slice_reports_the_window(capsys: pytest.CaptureFixture[str], source: Path) -> None:
    assert run("slice", "--text", str(source), "--start", "6", "--stop", "11") == 0
    printed = capsys.readouterr().out
    assert "window     [6..11)" in printed
    assert "bravo" in printed


def test_an_empty_window_answers_none(capsys: pytest.CaptureFixture[str], source: Path) -> None:
    assert run("slice", "--text", str(source), "--start", "5", "--stop", "5") == 1


def test_a_window_closing_downline_is_unusable(source: Path) -> None:
    assert run("slice", "--text", str(source), "--start", "9", "--stop", "2") == 2


def test_join_pairs_two_texts(
    capsys: pytest.CaptureFixture[str], source: Path, tmp_path: Path
) -> None:
    other = tmp_path / "other.txt"
    other.write_text("omega", encoding="utf-8")
    assert run("join", "--text", str(source), "--other", str(other)) == 0
    printed = capsys.readouterr().out
    assert TEXT + "omega" in printed


def test_split_rejoins_the_original(capsys: pytest.CaptureFixture[str], source: Path) -> None:
    assert run("split", "--text", str(source), "--at", "12") == 0
    printed = capsys.readouterr().out
    assert "rejoined   True" in printed


def test_selftest_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert run("selftest") == 0
    assert "0 failed" in capsys.readouterr().out


def test_a_missing_text_is_unusable(tmp_path: Path) -> None:
    assert run("load", "--text", str(tmp_path / "gone.txt")) == 2


def test_an_unknown_command_is_unusable() -> None:
    assert run("frobnicate") == 2
