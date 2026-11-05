from __future__ import annotations

from {{ package_name }} import verify as subject

BASE = "".join(f"line {n}\n" for n in range(1, 11))


def test_the_round_trip_reports_three_checks() -> None:
    verdict = subject.roundtrip(BASE, BASE.replace("line 3\n", "three\n"))
    assert verdict.ok
    assert len(verdict.checks) == 3
    assert [check.name for check in verdict.checks] == [
        "the patch parses",
        "apply reproduces the new text",
        "diffing the result is empty",
    ]


def test_identical_texts_pass_without_hunks() -> None:
    verdict = subject.roundtrip(BASE, BASE)
    assert verdict.ok
    assert verdict.checks[0].detail == "no hunks to parse"


def test_the_awkward_texts_pass_too() -> None:
    for label, old, new in (
        ("empty to one line", "", "x\n"),
        ("one line to empty", "x\n", ""),
        ("no final newline", "a\nb", "a\nc"),
        ("crlf kept", "a\r\nb\r\n", "a\r\nc\r\n"),
        ("blank lines", "a\n\n\nb\n", "a\n\nb\n"),
    ):
        assert subject.roundtrip(old, new).ok, label


def test_a_broken_check_makes_the_verdict_fail() -> None:
    verdict = subject.Verdict((subject.Check("x", True, "fine"), subject.Check("y", False, "no")))
    assert not verdict.ok
    assert verdict.lines() == ["ok   x                            fine",
                               "FAIL y                            no"]


def test_the_verdict_serialises() -> None:
    payload = subject.roundtrip("a\n", "b\n").as_dict()
    assert payload["ok"] is True
    assert len(payload["checks"]) == 3
    assert payload["checks"][0]["name"] == "the patch parses"
