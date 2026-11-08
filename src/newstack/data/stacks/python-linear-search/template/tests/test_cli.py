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


def test_search_exits_zero():
    assert _run(["search", "1", "3", "5", "7", "9", "5"]) == 0


def test_search_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _run(["search", "--json", "1", "3", "5", "7", "9", "5"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == 2


def test_contains_exits_zero():
    assert _run(["contains", "1", "3", "5", "7", "9", "5"]) == 0


def test_count_exits_zero():
    assert _run(["count", "1", "3", "5", "7", "9", "6"]) == 0


def test_audit_exits_zero():
    assert _run(["audit", "1", "3", "5", "7", "9"]) == 0


def test_demo_exits_zero():
    assert _run(["demo"]) == 0


def test_selftest_exits_zero():
    assert _run(["selftest"]) == 0


def test_negative_exits_two():
    assert _run(["search", "1", "2", "3", "1", "-1"]) == 2


def test_oor_exits_two():
    assert _run(["search", "1", "2", "3", "999"]) == 2


def test_long_project_name_imports():
    assert True
