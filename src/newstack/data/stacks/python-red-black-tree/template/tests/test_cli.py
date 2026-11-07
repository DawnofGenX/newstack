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
BODY = "# fixture\n\n7\n-13\n42\n"


def _write(tmp_path, body: str = BODY) -> str:
    path = tmp_path / KEYS
    path.write_text(body, encoding="utf-8")
    return str(path)


def run(*argv: str) -> tuple[int, str]:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), \
            contextlib.redirect_stderr(buffer):
        status = main(list(argv))
    return status, buffer.getvalue()


def test_version_and_help_exit_zero() -> None:
    assert build_parser().prog
    status, out = run("--version")
    assert status == EXIT_OK
    assert "0.1.0" in out


def test_membership_exits_on_the_answer(tmp_path) -> None:
    keys = _write(tmp_path)
    status, out = run("has", "--keys", keys, "7")
    assert status == EXIT_OK
    assert "7            key" in out
    status, out = run("has", "--keys", keys, "8")
    assert status == EXIT_MISS
    assert "not a key" in out
    status, _ = run("has", "--keys", keys, "7", "42")
    assert status == EXIT_OK
    status, _ = run("has", "--keys", keys, "7", "8")
    assert status == EXIT_MISS


def test_the_walk_is_sorted_and_the_json_agrees(tmp_path) -> None:
    keys = _write(tmp_path)
    status, out = run("iter", "--keys", keys)
    assert status == EXIT_OK
    assert "3 listed, ascending" in out
    status, out = run("iter", "--keys", keys, "--json")
    payload = json.loads(out)
    assert payload["walk"] == [-13, 7, 42]
    assert payload["seated"] is True


def test_an_empty_walk_admits_itself(tmp_path) -> None:
    keys = _write(tmp_path, "")
    status, _ = run("iter", "--keys", keys)
    assert status == EXIT_MISS


def test_add_and_remove_answer_in_public(tmp_path) -> None:
    keys = _write(tmp_path)
    status, out = run("add", "--keys", keys, "99")
    assert status == EXIT_OK
    assert "4 held, 1 added" in out
    status, out = run("add", "--keys", keys, "7")
    assert status == EXIT_OK
    assert "0 added" in out
    status, out = run("remove", "--keys", keys, "42")
    assert status == EXIT_OK
    assert "removed" in out
    status, out = run("remove", "--keys", keys, "8")
    assert status == EXIT_UNUSABLE
    assert "remove of an absent key" in out


def test_junk_is_refused_by_name(tmp_path) -> None:
    keys = _write(tmp_path)
    status, out = run("has", "--keys", keys, "1.5")
    assert status == EXIT_UNUSABLE
    assert "not a key" in out
    status, out = run("iter", "--keys", str(tmp_path / "missing.txt"))
    assert status == EXIT_UNUSABLE
    assert "no such key list" in out


def test_selftest_and_demo_answer_honest(tmp_path) -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
    status, out = run("demo")
    assert status == EXIT_OK
    assert "6 of 6 hold" in out
