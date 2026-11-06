"""The decision: which arm said yes, and why the others said no."""

from {{ package_name }} import explain as subject
from {{ package_name }} import ranges
from {{ package_name }}.version import parse


def test_an_accepted_version_names_the_arm():
    decision = subject.decide(parse("2.5.0"), ranges.parse_range("~1.4 || ^2.0"))
    assert decision.ok
    assert decision.arm == 2
    assert "arm 2" in decision.verdict()


def test_a_refused_version_explains_every_arm():
    decision = subject.decide(parse("1.5.0"), ranges.parse_range("~1.4 || ^2.0"))
    assert not decision.ok
    assert len(decision.reasons) == 2
    assert "upper bound" in decision.reasons[0]
    assert "below the lower bound" in decision.reasons[1]


def test_a_prerelease_refusal_says_prerelease():
    decision = subject.decide(parse("1.3.0-beta"), ranges.parse_range("^1.2.0"))
    assert not decision.ok
    assert "prerelease" in decision.reasons[0]


def test_an_excluded_bound_is_named():
    decision = subject.decide(parse("1.5.0"), ranges.parse_range(">=1.0.0 <1.5.0"))
    assert not decision.ok
    assert "excluded" in decision.reasons[0]


def test_an_empty_arm_says_so():
    decision = subject.decide(parse("1.5.0"), ranges.parse_range(">=2.0.0 <1.0.0"))
    assert not decision.ok
    assert "allows nothing" in decision.reasons[0]


def test_the_lines_name_the_version_and_the_verdict():
    decision = subject.decide(parse("1.9.9"), ranges.parse_range("^1.2.3"))
    lines = decision.lines()
    assert lines[0] == "version    1.9.9"
    assert lines[1] == "range      ^1.2.3"
    assert lines[2].startswith("verdict    satisfies")


def test_an_inclusion_reason_is_not_a_refusal():
    decision = subject.decide(parse("1.4.2"), ranges.parse_range("~1.4"))
    assert "inside" in decision.reasons[0]
