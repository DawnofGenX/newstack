from pathlib import Path

from {{ package_name }}.engine import Request, decide
from {{ package_name }}.policy import load

HERE = Path(__file__).resolve().parent.parent


def policy():
    return load(HERE / "fixtures" / "policy.json")


def test_an_inherited_role_allows_inside_the_scope():
    decision = decide(policy(), Request("alice", "docs:write", "project:acme/doc:42"))
    assert decision.allowed
    assert decision.winner == "allow-write"


def test_the_same_write_outside_the_scope_falls_through():
    decision = decide(policy(), Request("alice", "docs:write", "project:other/doc:42"))
    assert decision.effect == "default"
    assert decision.winner is None


def test_the_reason_names_the_missing_role():
    decision = decide(policy(), Request("carol", "docs:write", "project:acme/doc:42"))
    reasons = [item.because for item in decision.considered if item.rule.id == "allow-write"]
    assert reasons and "holds none of the roles" in reasons[0]


def test_a_deny_outranks_a_matching_allow():
    decision = decide(policy(), Request("carol", "docs:read", "project:acme/secret"))
    assert decision.effect == "deny"
    assert decision.winner == "deny-secret"
    matched = [item.rule.id for item in decision.considered if item.matched]
    assert matched == ["allow-read", "deny-secret"]


def test_a_subject_with_no_assignment_is_denied_by_default():
    decision = decide(policy(), Request("mallory", "docs:read", "project:acme/doc:1"))
    assert decision.effect == "default"
    assert "by default" in "\n".join(decision.lines())


def test_a_condition_can_grant():
    decision = decide(
        policy(),
        Request(
            "carol",
            "comments:create",
            "project:acme/doc:7",
            subject_attributes={"id": "carol"},
            resource_attributes={"owner": "carol"},
        ),
    )
    assert decision.allowed


def test_a_missing_attribute_does_not_grant():
    decision = decide(
        policy(),
        Request(
            "carol",
            "comments:create",
            "project:acme/doc:7",
            subject_attributes={"id": "carol"},
        ),
    )
    assert decision.effect == "default"
    reasons = [item.because for item in decision.considered if item.rule.id == "allow-comment"]
    assert "missing" in reasons[0]


def test_every_rule_is_reported_once():
    decision = decide(policy(), Request("alice", "docs:write", "project:acme/doc:1"))
    assert [item.rule.id for item in decision.considered] == [rule.id for rule in policy().rules]


def test_the_trace_is_deterministic():
    first = decide(policy(), Request("alice", "docs:read", "project:acme/doc:1"))
    second = decide(policy(), Request("alice", "docs:read", "project:acme/doc:1"))
    assert first.lines() == second.lines()


def test_the_decision_serialises():
    payload = decide(policy(), Request("alice", "docs:write", "project:acme/doc:1")).as_dict()
    assert payload["effect"] == "allow"
    assert payload["winner"] == "allow-write"
    assert isinstance(payload["considered"], list)
