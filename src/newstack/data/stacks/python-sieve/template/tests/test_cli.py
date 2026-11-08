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


def test_primes_exits_zero():
    assert _run(["primes", "10"]) == 0


def test_primes_json():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _run(["primes", "--json", "10"])
    assert rc == 0
    assert json.loads(buf.getvalue()) == [2, 3, 5, 7]


def test_is_prime_exits_zero():
    assert _run(["is_prime", "7"]) == 0


def test_count_exits_zero():
    assert _run(["count", "10"]) == 0


def test_audit_exits_zero():
    assert _run(["audit", "2", "5", "10", "30"]) == 0


def test_demo_exits_zero():
    assert _run(["demo"]) == 0


def test_selftest_exits_zero():
    assert _run(["selftest"]) == 0


def test_small_exits_two():
    assert _run(["primes", "1"]) == 2
