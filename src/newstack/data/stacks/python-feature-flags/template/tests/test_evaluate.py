"""The precedence table, and the reason that makes each answer explainable."""

from __future__ import annotations

import pytest

from {{ package_name }} import evaluate as subject
from {{ package_name }} import model


def flags() -> model.FlagSet:
    return model.FlagSet.of(
        [
            model.Flag(name="all", rollout=100, salt="all"),
            model.Flag(name="none", rollout=0, salt="none"),
            model.Flag(name="off", enabled=False, rollout=100, salt="off"),
            model.Flag(
                name="off-but-targeted",
                enabled=False,
                rollout=0,
                salt="obt",
                targets=frozenset({"alice"}),
            ),
            model.Flag(name="vip", rollout=0, salt="vip", targets=frozenset({"alice"})),
            model.Flag(name="half", rollout=50, salt="half"),
        ]
    )


def test_an_unknown_flag_is_off_and_says_unknown() -> None:
    decision = subject.decide(flags(), "nope", "alice")
    assert (decision.variant, decision.reason) == ("off", "unknown")


def test_the_kill_switch_beats_targeting() -> None:
    decision = subject.decide(flags(), "off-but-targeted", "alice")
    assert (decision.variant, decision.reason) == ("off", "off")


def test_targeting_beats_the_rollout() -> None:
    decision = subject.decide(flags(), "vip", "alice")
    assert (decision.variant, decision.reason) == ("on", "targeted")


def test_an_untargeted_user_on_a_zero_rollout_is_outside() -> None:
    decision = subject.decide(flags(), "vip", "carol")
    assert (decision.variant, decision.reason) == ("off", "outside")


def test_a_full_rollout_is_inside_for_everyone() -> None:
    assert subject.decide(flags(), "all", "whoever").reason == "inside"


def test_a_half_rollout_answers_the_same_twice() -> None:
    first = subject.decide(flags(), "half", "bob")
    second = subject.decide(flags(), "half", "bob")
    assert first == second


def test_the_decision_carries_the_arithmetic() -> None:
    decision = subject.decide(flags(), "half", "alice")
    assert decision.cutoff == 5000
    assert 0 <= decision.bucket < 10_000
    assert decision.on is (decision.bucket < 5000)


def test_a_decision_line_names_the_variant_reason_and_numbers() -> None:
    line = subject.decide(flags(), "all", "alice").line()
    assert line.startswith("on  inside    all")
    assert "bucket" in line and "<" in line


def test_the_payload_is_json_shaped() -> None:
    payload = subject.decide(flags(), "all", "alice").as_dict()
    assert set(payload) == {"flag", "user", "variant", "reason", "bucket", "cutoff", "rollout"}
    assert payload["variant"] == "on"


def test_an_unknown_reason_is_refused() -> None:
    with pytest.raises(ValueError, match="unknown reason"):
        subject.Decision("a", "u", "on", "vibes", 0, 0, 0)


def test_explain_shows_the_rules_in_order() -> None:
    lines = subject.explain(flags(), "half", "alice")
    assert lines[0] == "flag     half"
    assert any(line.startswith("bucket  ") for line in lines)
    assert any(line.startswith("cutoff  ") for line in lines)
    assert lines[-1].startswith("decision ")


def test_explain_admits_an_unknown_flag() -> None:
    lines = subject.explain(flags(), "nope", "alice")
    assert lines[-2] == "decision off (unknown)"
    assert lines[-1] == "known    no"
