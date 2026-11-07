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
    assert "root       99" in out
    status, out = run("remove", "--keys", keys, "3")
    assert status == EXIT_OK
    assert "removed    3" in out


def test_has_admits_and_denies(tmp_path) -> None:
    keys = _write(tmp_path)
    status, out = run("has", "--keys", keys, "42")
    assert status == EXIT_OK
    assert "seated     True" in out
    assert "root       42" in out
    status, out = run("has", "--keys", keys, "4242")
    assert status == EXIT_MISS
    assert "seated     False" in out


def test_iter_walks_the_sort(tmp_path) -> None:
    keys = _write(tmp_path)
    status, out = run("iter", "--keys", keys, "--json")
    assert status == EXIT_OK
    payload = json.loads(out)
    assert payload["walk"] == [-7, 3, 12, 42]


def test_min_and_max_ride_up(tmp_path) -> None:
    keys = _write(tmp_path)
    status, out = run("min", "--keys", keys)
    assert status == EXIT_OK
    assert "min        -7" in out
    status, out = run("max", "--keys", keys, "--json")
    assert status == EXIT_OK
    assert json.loads(out)["root"] == 42


def test_bad_input_is_refused(tmp_path) -> None:
    status, _ = run("iter", "--keys", str(tmp_path / "missing.txt"))
    assert status == EXIT_UNUSABLE
    noise = tmp_path / "noise.txt"
    noise.write_text("7.5\n", encoding="utf-8")
    status, _ = run("iter", "--keys", str(noise))
    assert status == EXIT_UNUSABLE
    keys = _write(tmp_path)
    status, _ = run("remove", "--keys", keys, "4242")
    assert status == EXIT_UNUSABLE


def test_selftest_and_demo_hold() -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
    status, out = run("demo")
    assert status == EXIT_OK
    assert "6 of 6 hold" in out
