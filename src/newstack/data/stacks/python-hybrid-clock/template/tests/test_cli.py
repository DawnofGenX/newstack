from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from {{ package_name }} import cli as subject

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def run(argv: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = subject.main(argv)
    except SystemExit as exited:
        code = int(exited.code or 0)
    return code, out.getvalue()


def test_the_demo_holds_every_story() -> None:
    code, out = run(["demo"])
    assert code == subject.EXIT_OK, out
    assert out.count("-> holds") == 6
    assert "BROKEN" not in out


def test_a_plan_prints_the_stamps_it_produced() -> None:
    code, out = run(["plan", "--plan", str(FIXTURES / "handoff.jsonl")])
    assert code == subject.EXIT_OK, out
    assert "send" in out
    assert "receive" in out
    assert "causal breaks 0" in out


def test_a_plan_reports_no_break_when_the_wall_steps_back() -> None:
    code, out = run(["plan", "--plan", str(FIXTURES / "step-back.jsonl")])
    assert code == subject.EXIT_OK, out
    assert "causal breaks 0" in out


def test_json_carries_the_nodes() -> None:
    code, out = run(["plan", "--plan", str(FIXTURES / "handoff.jsonl"), "--json"])
    payload = json.loads(out)
    assert code == subject.EXIT_OK
    assert payload["messages"] == 1
    assert payload["violations"] == []


def test_a_missing_plan_is_unusable() -> None:
    code, _ = run(["plan", "--plan", "/nonexistent/plan.jsonl"])
    assert code == subject.EXIT_UNUSABLE


def test_a_skew_beyond_the_bound_exits_one() -> None:
    code, out = run(
        ["plan", "--plan", str(FIXTURES / "handoff.jsonl"), "--max-skew", "100"]
    )
    assert code == subject.EXIT_BROKEN
    assert "past the 100 ms bound" in out


def test_a_stamp_reads_back() -> None:
    code, out = run(["stamp", "000001700000000000:0000003@a"])
    assert code == subject.EXIT_OK
    assert "(1700000000000, 3, 'a')" in out


def test_a_broken_stamp_is_unusable() -> None:
    code, _ = run(["stamp", "not a stamp"])
    assert code == subject.EXIT_UNUSABLE


def test_help_names_the_commands() -> None:
    code, out = run(["--help"])
    assert code == 0
    assert "plan" in out


def test_version_names_the_program() -> None:
    code, out = run(["--version"])
    assert code == 0
    assert subject.PROGRAM in out
