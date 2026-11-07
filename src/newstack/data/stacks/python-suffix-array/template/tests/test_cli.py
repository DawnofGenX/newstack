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

TEXTS = "texts.txt"


def _write(tmp_path, body: str = "# fixture\n\nbanana\nmississippi\n") -> str:
    path = tmp_path / TEXTS
    path.write_text(body, encoding="utf-8")
    return str(path)


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


def test_build_seats_the_starts(tmp_path) -> None:
    texts = _write(tmp_path)
    status, out = run("build", "--texts", texts)
    assert status == EXIT_OK
    assert "text       'banana'" in out
    assert "suffixes   6" in out
    _status, out = run("build", "--texts", texts, "--json")
    assert json.loads(out)["array"] == [5, 3, 1, 0, 4, 2]


def test_count_exits_on_the_census(tmp_path) -> None:
    texts = _write(tmp_path)
    assert run("count", "--texts", texts, "na")[0] == EXIT_OK
    assert run("count", "--texts", texts, "zz")[0] == EXIT_MISS
    _status, out = run("count", "--texts", texts, "na", "--json")
    payload = json.loads(out)
    assert payload["count"] == 2
    assert payload["positions"] == [4, 2]


def test_lrs_answers_the_tall_share(tmp_path) -> None:
    texts = _write(tmp_path)
    status, out = run("lrs", "--texts", texts)
    assert status == EXIT_OK
    assert "repeat     'ana'" in out
    _status, out = run("lrs", "--texts", _write(tmp_path, "abc\n"), "--json")
    assert json.loads(out)["repeat"] == ""
    assert run("lrs", "--texts", _write(tmp_path, "abc\n"))[0] == EXIT_MISS


def test_lcp_counts_the_share(tmp_path) -> None:
    texts = _write(tmp_path)
    status, out = run("lcp", "--texts", texts, "1", "3")
    assert status == EXIT_OK
    assert "shares     3" in out
    assert run("lcp", "--texts", texts, "0", "1")[0] == EXIT_MISS
    assert run("lcp", "--texts", texts, "0", "99")[0] == EXIT_UNUSABLE


def test_a_broken_input_is_unusable(tmp_path) -> None:
    assert run("build", "--texts", str(tmp_path / "missing.txt"))[0] == EXIT_UNUSABLE
    noise = _write(tmp_path, "banana\nBanana\n")
    status, _output = run("build", "--texts", noise)
    assert status == EXIT_UNUSABLE
    assert run("count", "--texts", _write(tmp_path), "Nan")[0] == EXIT_UNUSABLE


def test_selftest_and_demo_answer_clean(tmp_path) -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
    status, out = run("demo")
    assert status == EXIT_OK
    assert "6 of 6 hold" in out
