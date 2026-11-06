from __future__ import annotations

import contextlib
import io
import json

import pytest

from {{ package_name }}.cli import (
    EXIT_NONE,
    EXIT_OK,
    EXIT_UNUSABLE,
    build_parser,
    main,
)

KEYS = "keys.txt"


@pytest.fixture()
def keys_file(tmp_path) -> str:
    path = tmp_path / KEYS
    path.write_text("# fixture\n-7\n0\n3\n11\n16\n", encoding="utf-8")
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


def test_load_walks_the_fixture_in_order(keys_file: str) -> None:
    status, out = run("load", "--keys", keys_file, "--order", "2")
    assert status == EXIT_OK
    assert "band [1..3]" in out


def test_load_json_reports_the_band(keys_file: str) -> None:
    _status, out = run("load", "--keys", keys_file, "--json")
    payload = json.loads(out)
    assert payload["band"] == [2, 5]
    assert payload["keys"] == [-7, 0, 3, 11, 16]


def test_lookup_exits_on_what_it_holds(keys_file: str) -> None:
    assert run("lookup", "--keys", keys_file, "--key", "11")[0] == EXIT_OK
    assert run("lookup", "--keys", keys_file, "--key", "12")[0] == EXIT_NONE


def test_scan_exits_on_what_a_window_holds(keys_file: str) -> None:
    assert run("scan", "--keys", keys_file, "--low", "0", "--high", "12")[0] == EXIT_OK
    assert run("scan", "--keys", keys_file, "--low", "4", "--high", "10")[0] == EXIT_NONE
    assert run("scan", "--keys", keys_file, "--low", "9", "--high", "1")[0] == EXIT_UNUSABLE


def test_page_freezes_and_reads_back(keys_file: str, tmp_path) -> None:
    out = str(tmp_path / "tree.page")
    status, report = run("page", "--keys", keys_file, "--out", out)
    assert status == EXIT_OK
    assert "identical  True" in report


def test_a_missing_key_file_is_unusable(tmp_path) -> None:
    status, _ = run("load", "--keys", str(tmp_path / "gone.txt"))
    assert status == EXIT_UNUSABLE


def test_order_one_is_unusable(keys_file: str) -> None:
    assert run("load", "--keys", keys_file, "--order", "1")[0] == EXIT_UNUSABLE


def test_selftest_exits_zero() -> None:
    status, out = run("selftest")
    assert status == EXIT_OK
    assert "0 failed" in out
