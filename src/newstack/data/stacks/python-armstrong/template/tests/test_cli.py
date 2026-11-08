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


def test_check_exits_zero():
    assert _run(["check", "153"]) == 0


def test_check_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _run(["check", "--json", "153"])
    assert rc == 0
    assert json.loads(buf.getvalue()) is True


def test_sum_exits_zero():
    assert _run(["sum", "153"]) == 0


def test_audit_exits_zero():
    assert _run(["audit", "153", "370"]) == 0


def test_demo_exits_zero():
    assert _run(["demo"]) == 0


def test_selftest_exits_zero():
    assert _run(["selftest"]) == 0


def test_oversized_exits_two():
    assert _run(["check", "10000"]) == 2
