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

WORDS = "words.txt"


def _write(tmp_path, body: str = "# fixture\n\ncar\ncart\ndog\n") -> str:
    path = tmp_path / WORDS
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


def test_has_exits_on_membership(tmp_path) -> None:
    words = _write(tmp_path)
    assert run("has", "--words", words, "car")[0] == EXIT_OK
    assert run("has", "--words", words, "zebra")[0] == EXIT_MISS
    status, out = run("has", "--words", words, "car", "dog")
    assert status == EXIT_OK
    status, out = run("has", "--words", words, "car", "zebra")
    assert status == EXIT_MISS
    _status, out = run("has", "--words", words, "car", "--json")
    assert json.loads(out)["corpus"] == ["car", "cart", "dog"]


def test_prefix_lists_in_order(tmp_path) -> None:
    words = _write(tmp_path)
    status, out = run("prefix", "--words", words, "--prefix", "ca")
    assert status == EXIT_OK
    assert "under      2 word(s)" in out
    _status, out = run("prefix", "--words", words, "--prefix", "ca", "--json")
    assert json.loads(out)["listing"] == ["car", "cart"]
    assert run("prefix", "--words", words, "--prefix", "zz")[0] == EXIT_MISS


def test_count_names_the_size_and_the_stem(tmp_path) -> None:
    words = _write(tmp_path)
    status, out = run("count", "--words", words)
    assert status == EXIT_OK
    assert "words      3 held" in out
    assert "prefix     '' shared by all" in out
    shared = _write(tmp_path, "cart\ncar\ncat\n")
    _status, out = run("count", "--words", shared, "--json")
    assert json.loads(out)["words"] == 3


def test_delete_reports_the_landed_word(tmp_path) -> None:
    words = _write(tmp_path)
    status, out = run("delete", "--words", words, "dog")
    assert status == EXIT_OK
    assert "deleted    True, 2 remain" in out
    assert run("delete", "--words", words, "kitten")[0] == EXIT_MISS


def test_add_stores_and_reports(tmp_path) -> None:
    words = _write(tmp_path)
    status, out = run("add", "--words", words, "kitten")
    assert status == EXIT_OK
    assert "words      4 held" in out
    assert "kitten" in out


def test_a_broken_input_is_unusable(tmp_path) -> None:
    assert run("count", "--words", str(tmp_path / "missing.txt"))[0] == EXIT_UNUSABLE
    noise = _write(tmp_path, "car\nCart\n")
    status, _output = run("count", "--words", noise)
    assert status == EXIT_UNUSABLE
    assert run("has", "--words", _write(tmp_path), "Cart")[0] == EXIT_UNUSABLE


def test_selftest_and_demo_answer_clean(tmp_path) -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
    status, out = run("demo")
    assert status == EXIT_OK
    assert "6 of 6 hold" in out
