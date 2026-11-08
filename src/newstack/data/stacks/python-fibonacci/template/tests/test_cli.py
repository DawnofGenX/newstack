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


def test_fibonacci_exits_zero():
    assert _run(["fibonacci", "10"]) == 0


def test_fibonacci_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _run(["fibonacci", "--json", "10"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == 55


def test_list_exits_zero():
    assert _run(["list", "5"]) == 0


def test_audit_exits_zero():
    assert _run(["audit", "0", "1", "5", "10"]) == 0


def test_demo_exits_zero():
    assert _run(["demo"]) == 0


def test_selftest_exits_zero():
    assert _run(["selftest"]) == 0


def test_negative_exits_two():
    assert _run(["fibonacci", "-1"]) == 2
