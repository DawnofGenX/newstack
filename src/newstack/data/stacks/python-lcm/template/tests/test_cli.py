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


def test_lcm_exits_zero():
    assert _run(["lcm", "4", "6"]) == 0


def test_lcm_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _run(["lcm", "--json", "4", "6"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == 12


def test_gcd_exits_zero():
    assert _run(["gcd", "4", "6"]) == 0


def test_coprime_exits_zero():
    assert _run(["coprime", "3", "5"]) == 0


def test_audit_exits_zero():
    assert _run(["audit", "4,6", "3,5"]) == 0


def test_demo_exits_zero():
    assert _run(["demo"]) == 0


def test_selftest_exits_zero():
    assert _run(["selftest"]) == 0


def test_oversized_exits_two():
    assert _run(["lcm", "10000", "2"]) == 2
