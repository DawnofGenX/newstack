from __future__ import annotations

import json

import pytest

from {{ package_name }} import cli


def test_a_match_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["match", "a*b", "aaab"]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "the whole text matches" in out


def test_a_miss_exits_one(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["match", "a*b", "aaa"]) == cli.EXIT_NO_MATCH
    assert "no match for the whole text" in capsys.readouterr().out


def test_a_bad_pattern_is_unusable(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["match", "(ab", "x"]) == cli.EXIT_UNUSABLE
    err = capsys.readouterr().err
    assert "never closed" in err
    assert "^" in err


def test_a_search_reports_a_span(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["search", "a+", "xaay"]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "[1, 3) 'aa'" in out


def test_a_search_that_finds_nothing_exits_one() -> None:
    assert cli.main(["search", "z", "banana"]) == cli.EXIT_NO_MATCH


def test_explain_prints_the_state_sets(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["explain", "(cat|dog)s?", "dogs"]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "at  seen" in out
    assert "accepting" in out


def test_why_prints_the_verdict_before_the_trace(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["why", "a", "aa"]) == cli.EXIT_NO_MATCH
    out = capsys.readouterr().out
    assert out.index("verdict") < out.index("at  seen")


def test_machine_lists_every_state(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["machine", "a*"]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "no way out" in out


def test_dfa_reports_its_size(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["dfa", "(a|b)*abb"]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "state(s)" in out


def test_dfa_json_carries_the_counts(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["dfa", "(a|b)*abb", "--json"]) == cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["states"] >= 2
    assert payload["pattern"] == "(a|b)*abb"


def test_agrees_on_a_small_alphabet(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["agrees", "(a|b)*abb", "--alphabet", "ab", "--max-len", "5"]) == cli.EXIT_OK
    assert "the two machines agree" in capsys.readouterr().out


def test_agrees_refuses_a_negative_length() -> None:
    assert cli.main(["agrees", "a", "--max-len", "-1"]) == cli.EXIT_UNUSABLE


def test_compare_reports_both_engines(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["compare", "(a*)*b", "aaaa"]) == cli.EXIT_OK
    out = capsys.readouterr().out
    assert "simulation" in out
    assert "backtrack" in out
    assert "both engines agree" in out


def test_match_json_carries_the_span(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["match", "ab", "ab", "--json"]) == cli.EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == {
        "pattern": "ab",
        "text": "ab",
        "matched": True,
        "start": 0,
        "end": 2,
        "value": "ab",
    }


def test_version_names_the_program(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as caught:
        cli.main(["--version"])
    assert caught.value.code == 0
    assert cli.PROGRAM in capsys.readouterr().out


def test_the_subcommands_are_all_routed() -> None:
    parser = cli.build_parser()
    argvs = {
        "match": ["a", "a"],
        "search": ["a", "a"],
        "explain": ["a", "a"],
        "why": ["a", "a"],
        "machine": ["a"],
        "dfa": ["a"],
        "agrees": ["a"],
        "compare": ["a", "a"],
        "demo": [],
        "selftest": [],
    }
    for name, rest in argvs.items():
        assert parser.parse_args([name, *rest]).command == name


def test_demo_reports_every_story(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["demo"]) == cli.EXIT_OK
    assert "stories      6 of 6 hold" in capsys.readouterr().out


def test_selftest_reports_no_failures(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["selftest"]) == cli.EXIT_OK
    assert "0 failed" in capsys.readouterr().out
