from __future__ import annotations

import contextlib
import io
import json

from {{ package_name }}.calc import (
    value_of,
)
from {{ package_name }}.cli import (
    EXIT_BROKE,
    EXIT_OK,
    EXIT_UNUSABLE,
    build_parser,
    main,
)


def run(*argv: str):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        status = main(list(argv))
    return status, buffer.getvalue()


def run_err(*argv: str):
    buffer = io.StringIO()
    with contextlib.redirect_stderr(buffer):
        status = main(list(argv))
    return status, buffer.getvalue()


def test_version_and_help_exit_zero() -> None:
    assert build_parser().prog
    status, out = run("--version")
    assert status == EXIT_OK
    assert "0.1.0" in out


def test_eval_answers_the_documented_value() -> None:
    status, out = run("eval", "3 + 4 * 2 / ( 1 - 5 ) * 2")
    assert status == EXIT_OK
    assert "value      -1" in out
    status, out = run("eval", "2 + 3 * 4", "--json")
    assert status == EXIT_OK
    assert json.loads(out)["value"] == 14


def test_postfix_yields_the_documented_queue() -> None:
    status, out = run("postfix", "2 + 3 * 4")
    assert status == EXIT_OK
    assert "2 3 4 * +" in out


def test_a_divided_zero_exits_two() -> None:
    status, _ = run_err("eval", "5 / 0")
    assert status == EXIT_UNUSABLE
    assert EXIT_BROKE != EXIT_UNUSABLE


def test_an_unbalanced_paren_exits_two() -> None:
    status, out = run_err("eval", "( 1 + 2")
    assert status == EXIT_UNUSABLE
    assert "unbalanced" in out


def test_a_missing_ledger_exits_two() -> None:
    status, _ = run_err("report", "--corpus", "nowhere.txt")
    assert status == EXIT_UNUSABLE


def test_selftest_and_demo_answer_quiet() -> None:
    assert run("selftest")[0] == EXIT_OK
    status, out = run("demo")
    assert status == EXIT_OK
    assert "6 of 6 hold" in out
    assert value_of("7 / 2") == 3
