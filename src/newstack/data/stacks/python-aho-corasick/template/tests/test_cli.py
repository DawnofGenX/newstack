from __future__ import annotations

import contextlib
import io
import json

import pytest

from {{ package_name }}.cli import (
    EXIT_NONE,
    EXIT_OK,
    EXIT_UNUSABLE,
    build_parser,
    main,
)

PATTERNS = "patterns.txt"
TEXT = "text.txt"


@pytest.fixture()
def corpus(tmp_path) -> tuple[str, str]:
    patterns = tmp_path / PATTERNS
    patterns.write_text("# fixture\nhe\nshe\nhis\nhers\n", encoding="utf-8")
    text = tmp_path / TEXT
    text.write_text("ahishers", encoding="utf-8")
    return str(patterns), str(text)


def run(*argv: str) -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        status = main(list(argv))
    return status, buffer.getvalue()


def test_version_and_help_exit_zero() -> None:
    assert build_parser().prog
    status, out = run("--version")
    assert status == EXIT_OK
    assert "0.1.0" in out


def test_build_states_the_automaton(corpus: tuple[str, str]) -> None:
    patterns, _ = corpus
    status, out = run("build", "--patterns", patterns)
    assert status == EXIT_OK
    assert "patterns   4 stated" in out


def test_build_json_names_the_shapes(corpus: tuple[str, str]) -> None:
    patterns, _ = corpus
    _status, out = run("build", "--patterns", patterns, "--json")
    payload = json.loads(out)
    assert payload["patterns"] == ["he", "she", "his", "hers"]
    assert payload["states"] >= 9


def test_scan_exits_on_what_the_sweep_found(corpus: tuple[str, str]) -> None:
    patterns, text = corpus
    status, out = run("scan", "--patterns", patterns, "--text", text)
    assert status == EXIT_OK
    assert "'she' ends at 5" in out
    quiet = f"{text}.quiet"
    with open(quiet, "w", encoding="utf-8") as handle:
        handle.write("zzzz")
    assert run("scan", "--patterns", patterns, "--text", quiet)[0] == EXIT_NONE


def test_a_quiet_text_exits_one(corpus: tuple[str, str]) -> None:
    patterns, text = corpus
    quiet = f"{text}.quiet"
    with open(quiet, "w", encoding="utf-8") as handle:
        handle.write("zzz")
    assert run("scan", "--patterns", patterns, "--text", quiet)[0] == EXIT_NONE


def test_count_reports_the_sweep_and_the_naive(corpus: tuple[str, str]) -> None:
    patterns, text = corpus
    status, out = run("count", "--patterns", patterns, "--text", text)
    assert status == EXIT_OK
    assert "cheaper    True" in out


def test_the_demo_tells_the_counter_story() -> None:
    status, out = run("demo")
    assert status == EXIT_OK
    assert "equal to the naive scan" in out


def test_a_missing_pattern_file_is_unusable(tmp_path) -> None:
    status, _ = run("build", "--patterns", str(tmp_path / "gone.txt"))
    assert status == EXIT_UNUSABLE


def test_a_blank_pattern_is_unusable(tmp_path) -> None:
    blank = tmp_path / PATTERNS
    blank.write_text("\n", encoding="utf-8")
    text = tmp_path / TEXT
    text.write_text("a", encoding="utf-8")
    status, _ = run("scan", "--patterns", str(blank), "--text", str(text))
    assert status == EXIT_UNUSABLE


def test_selftest_exits_zero() -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
