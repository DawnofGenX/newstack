from __future__ import annotations

import contextlib
import io
import json

from {{ package_name }} import cli as subject


def run(argv: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = subject.main(argv)
    except SystemExit as exited:
        code = int(exited.code or 0)
    return code, out.getvalue()


def test_simulate_exits_zero_without_a_gate() -> None:
    code, out = run(["simulate", "--policy", "fixed", "--clients", "20"])
    assert code == subject.EXIT_OK
    assert "peak" in out


def test_a_breached_peak_exits_one_and_says_so() -> None:
    code, out = run(["simulate", "--policy", "fixed", "--clients", "20", "--max-peak", "5"])
    assert code == subject.EXIT_BREACH
    assert "BREACH" in out


def test_a_held_peak_exits_zero() -> None:
    code, out = run(
        ["simulate", "--policy", "full-jitter", "--clients", "200", "--max-peak", "60"]
    )
    assert code == subject.EXIT_OK, out
    assert "ok" in out


def test_json_names_the_policy_and_the_peak() -> None:
    code, out = run(["simulate", "--policy", "exponential", "--clients", "30", "--json"])
    payload = json.loads(out)
    assert code == subject.EXIT_OK
    assert payload["peak_retries"] == 30
    assert payload["policy"].startswith("exponential")


def test_an_unknown_policy_exits_two() -> None:
    code, _ = run(["simulate", "--policy", "magic"])
    assert code == subject.EXIT_UNUSABLE


def test_a_zero_client_count_is_refused_by_the_cli() -> None:
    code, _ = run(["simulate", "--policy", "fixed", "--clients", "0"])
    assert code == subject.EXIT_UNUSABLE


def test_compare_prints_every_policy() -> None:
    code, out = run(["compare", "--clients", "40"])
    assert code == subject.EXIT_OK
    for needle in ("fixed", "exponential", "full jitter", "equal jitter", "decorrelated"):
        assert needle in out
    assert "pile-up" in out


def test_demo_holds_every_story() -> None:
    code, out = run(["demo"])
    assert code == subject.EXIT_OK, out
    assert "BROKEN" not in out
    assert out.count("-> holds") == 6


def test_selftest_reports_success() -> None:
    code, out = run(["selftest"])
    assert code == subject.EXIT_OK, out
    assert "checks passed" in out


def test_version_prints_the_program_name() -> None:
    code, out = run(["--version"])
    assert code == 0
    assert subject.PROGRAM in out
