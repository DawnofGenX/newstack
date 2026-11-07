from __future__ import annotations

import contextlib
import io
import json

from {{ package_name }}.cli import (
    EXIT_BROKE,
    EXIT_OK,
    EXIT_UNUSABLE,
    build_parser,
    main,
)
from {{ package_name }}.coder import (
    compress,
    decompress,
)


def run(*argv: str) -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        status = main(list(argv))
    return status, buffer.getvalue()


def run_err(*argv: str) -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stderr(buffer):
        status = main(list(argv))
    return status, buffer.getvalue()


def test_version_and_help_exit_zero() -> None:
    assert build_parser().prog
    status, out = run("--version")
    assert status == EXIT_OK
    assert "0.1.0" in out


def test_compress_prices_the_repeat() -> None:
    status, out = run("compress", "abracadabraabracadabra")
    assert status == EXIT_OK
    assert "text       22 letters" in out
    status, out = run("compress", "abracadabraabracadabra", "--json")
    assert status == EXIT_OK
    json.loads(out)


def test_roundtrip_reports_the_closed_loop() -> None:
    status, out = run("roundtrip", "mississippimississippi")
    assert status == EXIT_OK
    assert "closed     True" in out


def test_decompress_hands_back_the_letters() -> None:
    stream = json.dumps([["a", "a"], ["a", "b"], ["b", 2, 4]])
    status, out = run("decompress", stream)
    assert status == EXIT_OK
    assert "ababab" in out


def test_a_loud_text_exits_two() -> None:
    status, _ = run_err("compress", "Abra")
    assert status == EXIT_UNUSABLE
    assert EXIT_BROKE != EXIT_UNUSABLE


def test_a_missing_corpus_exits_two() -> None:
    status, _ = run_err("report", "--corpus", "nowhere.txt")
    assert status == EXIT_UNUSABLE


def test_selftest_and_demo_answer_quiet() -> None:
    assert run("selftest")[0] == EXIT_OK
    status, out = run("demo")
    assert status == EXIT_OK
    assert "6 of 6 hold" in out
    assert run("roundtrip", "abracadabra", "--json")[1]
    payload = json.loads(run("roundtrip", "abra", "--json")[1])
    assert payload["closed"] is True
    assert decompress(compress("abra")) == "abra"
