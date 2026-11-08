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


def test_factorial_exits_zero():
    assert _run(["factorial", "5"]) == 0


def test_factorial_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _run(["factorial", "--json", "5"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == 120


def test_binomial_exits_zero():
    assert _run(["binomial", "5", "2"]) == 0


def test_audit_exits_zero():
    assert _run(["audit", "0", "1", "5", "10"]) == 0


def test_demo_exits_zero():
    assert _run(["demo"]) == 0


def test_selftest_exits_zero():
    assert _run(["selftest"]) == 0


def test_negative_exits_two():
    assert _run(["factorial", "-1"]) == 2
