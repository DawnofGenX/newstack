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
from {{ package_name }}.hashing import (
    BASE,
    MODULUS,
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


def test_find_reports_the_starts() -> None:
    status, out = run("find", "--pattern", "ana", "banana")
    assert status == EXIT_OK
    assert "starts     [1, 3]" in out
    status, out = run("find", "--pattern", "ana", "banana", "--json")
    assert json.loads(out)["starts"] == [1, 3]
    assert run("find", "--pattern", "zzz", "banana")[0] == EXIT_MISS


def test_count_reports_the_starts_measured() -> None:
    status, out = run("count", "--pattern", "ana", "banana")
    assert status == EXIT_OK
    assert "count      2" in out
    assert run("count", "--pattern", "zzz", "banana")[0] == EXIT_MISS


def test_digest_reports_the_documented_hash() -> None:
    status, out = run("digest", "--pattern", "ana", "--json")
    assert status == EXIT_OK
    payload = json.loads(out)
    assert payload["base"] == BASE
    assert payload["modulus"] == MODULUS
    assert payload["digest"] == BASE * BASE + 14 * BASE + 1
    status, out = run("digest", "--pattern", "a")
    assert status == EXIT_OK
    assert "digest     1" in out


def test_the_empty_pattern_sits_everywhere() -> None:
    status, out = run("count", "--pattern", "", "abra")
    assert status == EXIT_OK
    assert "count      5" in out


def test_a_long_pattern_never_sits() -> None:
    assert run("find", "--pattern", "abracadabra", "a")[0] == EXIT_MISS


def test_selftest_and_demo_answer_in_the_cli() -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
    status, out = run("demo")
    assert status == EXIT_OK
    assert "6 of 6 hold" in out


def test_a_loud_string_is_unusable() -> None:
    assert run("find", "--pattern", "Abra", "abra")[0] == EXIT_UNUSABLE
    assert run("find", "--pattern", "a", "a b")[0] == EXIT_UNUSABLE
    assert run("digest", "--pattern", "ab1")[0] == EXIT_UNUSABLE
    assert run("digest", "--pattern", "Abra")[0] == EXIT_UNUSABLE
