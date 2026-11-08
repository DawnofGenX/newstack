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


def test_count_exits_zero():
    assert _run(["count", "a b"]) == 0


def test_count_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _run(["count", "--json", "a b"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == 3


def test_freq_exits_zero():
    assert _run(["freq", "aab"]) == 0


def test_common_exits_zero():
    assert _run(["common", "aab"]) == 0


def test_audit_exits_zero():
    assert _run(["audit", "a b", "x"]) == 0


def test_demo_exits_zero():
    assert _run(["demo"]) == 0


def test_selftest_exits_zero():
    assert _run(["selftest"]) == 0


def test_oversized_exits_two():
    assert _run(["count", "a" * 1001]) == 2
