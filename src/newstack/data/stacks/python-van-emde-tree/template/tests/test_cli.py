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


def _write(tmp_path, body: str = "# fixture\n\n3\n17\n99\n255\n") -> str:
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
    status, out = run("add", "--keys", keys, "77")
    assert status == EXIT_OK
    assert "seats      5" in out
    status, out = run("add", "--keys", keys, "3")
    assert "seats      4" in out
    status, out = run("remove", "--keys", keys, "3")
    assert status == EXIT_OK
    assert "seats      3" in out


def test_has_seeks_answer_by_scan(tmp_path) -> None:
    keys = _write(tmp_path)
    status, out = run("has", "--keys", keys, "99")
    assert status == EXIT_OK and "seated     True" in out
    assert run("has", "--keys", keys, "100")[0] == EXIT_MISS
    status, out = run("succ", "--keys", keys, "100", "--json")
    assert json.loads(out)["successor"] == 255
    status, out = run("pred", "--keys", keys, "100", "--json")
    assert json.loads(out)["predecessor"] == 99


def test_min_and_max_answer(tmp_path) -> None:
    keys = _write(tmp_path)
    status, out = run("min", "--keys", keys)
    assert status == EXIT_OK and "min        3" in out
    status, out = run("max", "--keys", keys, "--json")
    assert json.loads(out)["max"] == 255
    empty = _write(tmp_path, "# none\n")
    assert run("min", "--keys", empty)[0] == EXIT_UNUSABLE


def test_a_broken_input_is_unusable(tmp_path) -> None:
    assert run("succ", "--keys", str(tmp_path / "missing.txt"), "7")[0] == EXIT_UNUSABLE
    assert run("remove", "--keys", _write(tmp_path), "100")[0] == EXIT_UNUSABLE
    noise = _write(tmp_path, "7\n1.5\n")
    assert run("succ", "--keys", noise, "7")[0] == EXIT_UNUSABLE
    away = _write(tmp_path, "999\n")
    assert run("succ", "--keys", away, "7")[0] == EXIT_UNUSABLE


def test_selftest_and_demo_answer_clean() -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
    status, out = run("demo")
    assert status == EXIT_OK
    assert "6 of 6 hold" in out
