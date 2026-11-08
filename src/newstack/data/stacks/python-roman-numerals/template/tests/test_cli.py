"""The command line, exercised as a user would run it."""

from __future__ import annotations

import contextlib
import io
import json

from {{ package_name }}.cli import main


def test_version_exits_zero():
    assert main(["--version"]) == 0


def test_encode_exits_zero():
    assert main(["encode", "10"]) == 0


def test_encode_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["encode", "--json", "10"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == "X"


def test_decode_exits_zero():
    assert main(["decode", "X"]) == 0


def test_decode_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["decode", "--json", "X"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == 10


def test_audit_exits_zero():
    assert main(["audit", "10,X", "42,XLII"]) == 0


def test_demo_exits_zero():
    assert main(["demo"]) == 0


def test_selftest_exits_zero():
    assert main(["selftest"]) == 0


def test_oversized_exits_two():
    assert main(["encode", "0"]) == 2
