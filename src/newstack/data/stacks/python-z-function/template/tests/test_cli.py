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
    with contextlib.redirect_stdout(buffer):
        status = main(list(argv))
    return status, buffer.getvalue()


def test_version_and_help_exit_zero() -> None:
    assert build_parser().prog
    status, out = run("--version")
    assert status == EXIT_OK
    assert "0.1.0" in out


def test_zarray_reports_the_array() -> None:
    status, out = run("zarray", "--word", "anana")
    assert status == EXIT_OK
    assert "array      [5, 0, 3, 0, 1]" in out
    status, out = run("zarray", "--word", "anana", "--json")
    assert json.loads(out)["array"] == [5, 0, 3, 0, 1]


def test_occurrences_reports_the_starts() -> None:
    status, out = run("occurrences", "--pattern", "ana", "banana")
    assert status == EXIT_OK
    assert "starts     [1, 3]" in out
    assert "first      1" in out
    status, out = run("occurrences", "--pattern", "ana", "banana", "--json")
    assert json.loads(out)["starts"] == [1, 3]
    assert run("occurrences", "--pattern", "zzz", "banana")[0] == EXIT_MISS


def test_count_reports_the_starts_measured() -> None:
    status, out = run("count", "--pattern", "ana", "banana")
    assert status == EXIT_OK
    assert "count      2" in out
    assert run("count", "--pattern", "zzz", "banana")[0] == EXIT_MISS


def test_the_empty_word_and_pattern_are_honest() -> None:
    status, out = run("zarray", "--word", "", "--json")
    assert status == EXIT_OK
    assert json.loads(out)["array"] == []
    status, out = run("count", "--pattern", "", "abra")
    assert status == EXIT_OK
    assert "count      5" in out


def test_a_long_pattern_never_sits() -> None:
    assert run("occurrences", "--pattern", "abracadabra", "a")[0] == EXIT_MISS


def test_selftest_and_demo_answer_in_the_cli() -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
    status, out = run("demo")
    assert status == EXIT_OK
    assert "6 of 6 hold" in out


def test_a_loud_string_is_unusable() -> None:
    assert run("zarray", "--word", "Abra")[0] == EXIT_UNUSABLE
    assert run("occurrences", "--pattern", "a", "a b")[0] == EXIT_UNUSABLE
    assert run("count", "--pattern", "ab1", "abra")[0] == EXIT_UNUSABLE
