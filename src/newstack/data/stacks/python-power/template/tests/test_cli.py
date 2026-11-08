"""The command line, exercised as a user would run it."""

from __future__ import annotations

import contextlib
import io
import json

from {{ package_name }}.cli import main


def test_version_exits_zero():
    assert main(["--version"]) == 0


def test_pow_exits_zero():
    assert main(["pow", "2", "10"]) == 0


def test_pow_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["pow", "--json", "2", "10"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == 1024


def test_mod_exits_zero():
    assert main(["mod", "2", "10", "1000"]) == 0


def test_audit_exits_zero():
    assert main(["audit", "2,10", "3,5"]) == 0


def test_demo_exits_zero():
    assert main(["demo"]) == 0


def test_selftest_exits_zero():
    assert main(["selftest"]) == 0


def test_oversized_exits_two():
    assert main(["pow", "2", "1001"]) == 2
