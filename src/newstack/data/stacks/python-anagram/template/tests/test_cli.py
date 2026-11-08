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


def test_is_anagram_exits_zero():
    assert _run(["is_anagram", "listen", "silent"]) == 0


def test_is_anagram_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _run(["is_anagram", "--json", "listen", "silent"])
    assert rc == 0
    assert json.loads(buf.getvalue()) is True


def test_signature_exits_zero():
    assert _run(["signature", "abc"]) == 0


def test_audit_exits_zero():
    assert _run(["audit", "listen", "silent", "abc", "def"]) == 0


def test_demo_exits_zero():
    assert _run(["demo"]) == 0


def test_selftest_exits_zero():
    assert _run(["selftest"]) == 0


def test_oversized_exits_two():
    assert _run(["is_anagram", "a" * 100, "a"]) == 2
