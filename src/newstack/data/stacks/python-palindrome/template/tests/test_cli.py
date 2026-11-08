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


def test_is_palindrome_exits_zero():
    assert _run(["is_palindrome", "aba"]) == 0


def test_is_palindrome_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _run(["is_palindrome", "--json", "aba"])
    assert rc == 0
    assert json.loads(buf.getvalue()) is True


def test_reverse_exits_zero():
    assert _run(["reverse", "ab"]) == 0


def test_audit_exits_zero():
    assert _run(["audit", "aba", "ab"]) == 0


def test_demo_exits_zero():
    assert _run(["demo"]) == 0


def test_selftest_exits_zero():
    assert _run(["selftest"]) == 0


def test_reverse_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _run(["reverse", "--json", "ab"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == "ba"
