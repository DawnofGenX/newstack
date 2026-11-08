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


def test_gcd_exits_zero():
    assert _run(["gcd", "12", "8"]) == 0


def test_gcd_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _run(["gcd", "--json", "12", "8"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == 4


def test_lcm_exits_zero():
    assert _run(["lcm", "4", "6"]) == 0


def test_coprime_exits_zero():
    assert _run(["coprime", "7", "5"]) == 0


def test_audit_exits_zero():
    assert _run(["audit", "2", "4", "3", "5"]) == 0


def test_demo_exits_zero():
    assert _run(["demo"]) == 0


def test_selftest_exits_zero():
    assert _run(["selftest"]) == 0


def test_zero_exits_two():
    assert _run(["gcd", "0", "5"]) == 2
