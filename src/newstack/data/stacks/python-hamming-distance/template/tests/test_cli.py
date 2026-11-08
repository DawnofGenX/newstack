"""The command line, exercised as a user would run it."""

from __future__ import annotations

import contextlib
import io
import json

from {{ package_name }}.cli import main


def test_version_exits_zero():
    assert main(["--version"]) == 0


def test_bits_exits_zero():
    assert main(["bits", "7", "11"]) == 0


def test_bits_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["bits", "--json", "7", "11"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == 2


def test_chars_exits_zero():
    assert main(["chars", "abc", "axc"]) == 0


def test_chars_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = main(["chars", "--json", "abc", "axc"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == 1


def test_audit_exits_zero():
    assert main(["audit", "7,11,2", "0,0,0"]) == 0


def test_demo_exits_zero():
    assert main(["demo"]) == 0


def test_selftest_exits_zero():
    assert main(["selftest"]) == 0


def test_oversized_exits_two():
    assert main(["bits", "1024", "0"]) == 2
