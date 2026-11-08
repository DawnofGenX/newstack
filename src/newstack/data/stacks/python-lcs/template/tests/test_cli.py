"""The command line, exercised as a user would run it."""

from __future__ import annotations

import contextlib
import io
import json

from {{ package_name }}.cli import main


def test_version_exits_zero():
    assert main(["--version"]) == 0


def test_lcs_exits_zero():
    assert main(["lcs", "abcde", "ace"]) == 0


def test_lcs_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["lcs", "--json", "abcde", "ace"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == "ace"


def test_len_exits_zero():
    assert main(["len", "abcde", "ace"]) == 0


def test_audit_exits_zero():
    assert main(["audit", "abcde,ace", "abc,abc"]) == 0


def test_demo_exits_zero():
    assert main(["demo"]) == 0


def test_selftest_exits_zero():
    assert main(["selftest"]) == 0


def test_oversized_exits_two():
    assert main(["lcs", "a" * 65, "b"]) == 2
