"""The command line, exercised as a user would run it."""

from __future__ import annotations

import contextlib
import io
import json

from {{ package_name }}.cli import main


def _run(argv):
    return main(argv)


def test_version_exits_zero():
    assert _run(["--version"]) == 0


def test_count_exits_zero():
    assert _run(["count", "hello"]) == 0


def test_count_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _run(["count", "--json", "hello"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == 2


def test_positions_exits_zero():
    assert _run(["positions", "hello"]) == 0


def test_is_vowel_exits_zero():
    assert _run(["is_vowel", "a"]) == 0


def test_audit_exits_zero():
    assert _run(["audit", "hello", "xyz"]) == 0


def test_demo_exits_zero():
    assert _run(["demo"]) == 0


def test_selftest_exits_zero():
    assert _run(["selftest"]) == 0


def test_oversized_exits_two():
    assert _run(["count", "a" * 100]) == 2
