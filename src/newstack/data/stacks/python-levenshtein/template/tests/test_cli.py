from __future__ import annotations

import contextlib
import io
import json

from {{ package_name }}.cli import (
    EXIT_MISS,
    EXIT_OK,
    EXIT_UNUSABLE,
    build_parser,
    main,
)


def run(*argv: str) -> tuple[int, str]:
    buffer = io.StringIO()
    errors = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(errors):
        status = main(list(argv))
    return status, buffer.getvalue() + errors.getvalue()


def write_words(tmp_path, body: str = "# fixture\n\ncar\ncart\ncat\ndog\n") -> str:
    path = tmp_path / "words.txt"
    path.write_text(body, encoding="utf-8")
    return str(path)


def test_version_and_help_exit_zero() -> None:
    assert build_parser().prog
    status, out = run("--version")
    assert status == EXIT_OK
    assert "0.1.0" in out
    status, out = run("--help")
    assert status == EXIT_OK
    assert "selftest" in out


def test_distance_answers_in_unit_steps() -> None:
    status, out = run("distance", "cart", "cat")
    assert status == EXIT_OK
    assert "distance   1" in out
    status, out = run("distance", "cat", "cat")
    assert status == EXIT_OK
    assert "distance   0" in out


def test_distance_reports_json_when_asked() -> None:
    status, out = run("distance", "knight", "light", "--json")
    assert status == EXIT_OK
    assert json.loads(out)["distance"] == 2


def test_an_empty_side_is_a_change_per_letter() -> None:
    status, out = run("distance", "cart", "")
    assert status == EXIT_OK
    assert "distance   4" in out


def test_nearest_exits_on_distance(tmp_path) -> None:
    words = write_words(tmp_path)
    status, out = run("nearest", "--words", words, "cat")
    assert status == EXIT_OK
    assert "nearest    'cat' at 0" in out
    status, out = run("nearest", "--words", words, "crt")
    assert status == EXIT_MISS
    assert "nearest    'cart' at 1" in out


def test_nearest_names_the_tied_words(tmp_path) -> None:
    words = write_words(tmp_path)
    status, out = run("nearest", "--words", words, "crt", "--json")
    assert status == EXIT_MISS
    payload = json.loads(out)
    assert payload["nearest"] == "cart"
    assert payload["tied"] == ["cart", "cat"]


def test_a_bad_query_is_refused_by_the_gate(tmp_path) -> None:
    words = write_words(tmp_path)
    status, _ = run("nearest", "--words", words, "Cat")
    assert status == EXIT_UNUSABLE


def test_a_missing_word_list_is_unusable(tmp_path) -> None:
    status, out = run("nearest", "--words", str(tmp_path / "gone.txt"), "cat")
    assert status == EXIT_UNUSABLE
    assert "no such word list" in out


def test_selftest_and_demo_answer_from_the_command_line() -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
    status, out = run("demo")
    assert status == EXIT_OK
    assert "6 of 6 hold" in out
