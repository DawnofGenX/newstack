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

KEYS = "keys.txt"


def _write(tmp_path, body: str = "# fixture\n\n3\n-7\n12\n42\n") -> str:
    path = tmp_path / KEYS
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


def test_add_and_remove_seat_and_unseat(tmp_path) -> None:
    keys = _write(tmp_path)
    status, out = run("add", "--keys", keys, "99")
    assert status == EXIT_OK
    assert "keys       5" in out
    status, out = run("add", "--keys", keys, "42")
    assert "keys       4" in out
    status, out = run("remove", "--keys", keys, "42")
    assert status == EXIT_OK
    assert "keys       3" in out


def test_has_answers_by_lookup(tmp_path) -> None:
    keys = _write(tmp_path)
    status, out = run("has", "--keys", keys, "42")
    assert status == EXIT_OK
    assert "seated     True" in out
    assert run("has", "--keys", keys, "99")[0] == EXIT_MISS


def test_iter_walks_the_sort(tmp_path) -> None:
    keys = _write(tmp_path)
    status, out = run("iter", "--keys", keys, "--json")
    assert status == EXIT_OK
    assert json.loads(out)["walk"] == [-7, 3, 12, 42]


def test_height_answers_over_a_seated_tree(tmp_path) -> None:
    assert run("height", "--keys", _write(tmp_path))[0] == EXIT_OK
    assert run("height", "--keys", _write(tmp_path, "7\n7\n"))[0] == EXIT_OK
    assert run("height", "--keys", _write(tmp_path, "# none\n"))[0] == EXIT_UNUSABLE


def test_a_broken_input_is_unusable(tmp_path) -> None:
    assert run("iter", "--keys", str(tmp_path / "missing.txt"))[0] == EXIT_UNUSABLE
    assert run("remove", "--keys", _write(tmp_path), "999")[0] == EXIT_UNUSABLE
    noise = _write(tmp_path, "7\n1.5\n")
    assert run("iter", "--keys", noise)[0] == EXIT_UNUSABLE


def test_selftest_and_demo_answer_clean() -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
    status, out = run("demo")
    assert status == EXIT_OK
    assert "6 of 6 hold" in out
