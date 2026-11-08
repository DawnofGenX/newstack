"""The command line, exercised as a user would run it."""

from __future__ import annotations

import contextlib
import io
import json

from {{ package_name }}.cli import main


def test_version_exits_zero():
    assert main(["--version"]) == 0


def test_convert_exits_zero():
    assert main(["convert", "10"]) == 0


def test_convert_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["convert", "--json", "10"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == "1010"


def test_read_exits_zero():
    assert main(["read", "1010"]) == 0


def test_read_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["read", "--json", "1010"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == 10


def test_audit_exits_zero():
    assert main(["audit", "10,1010", "7,111"]) == 0


def test_demo_exits_zero():
    assert main(["demo"]) == 0


def test_selftest_exits_zero():
    assert main(["selftest"]) == 0


def test_oversized_exits_two():
    assert main(["convert", "1024"]) == 2