"""Matching: the last rule wins, and a parent cannot be undone."""

from __future__ import annotations

import pytest

from {{ package_name }} import matcher as subject


def build(rules: list[str]) -> subject.Matcher:
    matcher, _ = subject.Matcher.from_lines(rules)
    return matcher


def test_the_last_matching_rule_decides() -> None:
    matcher = build(["*.log", "!keep.log"])
    assert matcher.ignored("debug.log")
    assert not matcher.ignored("keep.log")
    assert build(["!keep.log", "*.log"]).ignored("keep.log")


def test_the_verdict_names_the_rule_that_decided() -> None:
    verdict = build(["*.log", "!keep.log"]).decide("keep.log")
    assert verdict.ignored is False
    assert verdict.rule is not None
    assert verdict.rule.line == 2
    assert "negation" in verdict.reason


def test_a_bare_name_matches_at_any_depth_and_a_rooted_one_does_not() -> None:
    assert build(["build"]).ignored("sub/build", is_dir=True)
    assert not build(["/build"]).ignored("sub/build", is_dir=True)
    assert build(["/build"]).ignored("build", is_dir=True)


def test_a_directory_rule_ignores_what_is_inside_it() -> None:
    matcher = build(["build/"])
    assert not matcher.ignored("build")
    verdict = matcher.decide("build/out/app.js")
    assert verdict.ignored
    assert verdict.parent == "build"
    assert "parent" in verdict.reason


def test_a_negation_cannot_rescue_a_file_inside_an_excluded_directory() -> None:
    blocked = build(["build/", "!build/keep.txt"])
    assert blocked.ignored("build/keep.txt")
    assert blocked.decide("build/keep.txt").parent == "build"
    reachable = build(["build/*", "!build/keep.txt"])
    assert not reachable.ignored("build/keep.txt")


def test_one_star_stops_at_a_slash_and_two_stars_do_not() -> None:
    assert build(["logs/*.log"]).ignored("logs/a.log")
    assert not build(["logs/*.log"]).ignored("logs/x/a.log")
    assert build(["logs/**/*.log"]).ignored("logs/x/a.log")


def test_a_path_without_a_rule_is_tracked() -> None:
    verdict = build(["*.log"]).decide("main.py")
    assert verdict.ignored is False
    assert verdict.rule is None
    assert "nothing to ignore" in verdict.reason


def test_a_leading_dot_slash_is_stripped() -> None:
    assert build(["build/"]).decide("./build", is_dir=True).path == "build"


@pytest.mark.parametrize("path", ["", "../escape", "a//b"])
def test_a_path_that_cannot_be_matched_is_refused(path: str) -> None:
    with pytest.raises(subject.PathError):
        build(["*.log"]).decide(path)


def test_a_matcher_needs_rules() -> None:
    with pytest.raises(subject.PatternError):
        subject.Matcher([])


def test_a_walk_reports_every_path_it_sees(tmp_path) -> None:
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "out.js").write_text("x", encoding="utf-8")
    (tmp_path / "app.log").write_text("x", encoding="utf-8")
    (tmp_path / "main.py").write_text("x", encoding="utf-8")
    verdicts = build(["build/", "*.log"]).walk(tmp_path)
    ignored = sorted(verdict.path for verdict in verdicts if verdict.ignored)
    assert len(verdicts) == 4
    assert ignored == ["app.log", "build", "build/out.js"]


def test_a_missing_ignore_file_is_refused(tmp_path) -> None:
    with pytest.raises(subject.PatternError):
        subject.Matcher.from_file(tmp_path / "absent")
