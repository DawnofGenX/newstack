import json
from pathlib import Path

import pytest

from {{ package_name }}.policy import PolicyError, load, parse

HERE = Path(__file__).resolve().parent.parent


def test_the_shipped_fixture_loads():
    policy = load(HERE / "fixtures" / "policy.json")
    assert set(policy.roles) == {"viewer", "editor", "auditor"}
    assert len(policy.rules) == 4


def test_a_chain_includes_inherited_roles_in_order():
    policy = load(HERE / "fixtures" / "policy.json")
    assert policy.chain("editor") == ("editor", "viewer")
    assert policy.chain("auditor") == ("auditor", "viewer")


def test_an_assignment_carries_its_scope():
    policy = load(HERE / "fixtures" / "policy.json")
    scopes = {a.subject: a.scope for a in policy.assignments}
    assert scopes["alice"] == "project:acme"
    assert scopes["carol"] is None


def test_held_roles_follow_the_scope():
    policy = load(HERE / "fixtures" / "policy.json")
    inside = {name for name, _ in policy.held("alice", "project:acme/doc:1")}
    outside = {name for name, _ in policy.held("alice", "project:other/doc:1")}
    assert inside == {"editor", "viewer"}
    assert outside == set()


def test_an_inheritance_cycle_is_refused():
    with pytest.raises(PolicyError, match="inherits itself"):
        parse(
            {
                "roles": {"a": {"inherits": ["b"]}, "b": {"inherits": ["a"]}},
                "assignments": [],
                "rules": [],
            }
        )


def test_an_unknown_role_in_a_rule_is_refused():
    with pytest.raises(PolicyError, match="unknown role"):
        parse(
            {
                "roles": {},
                "assignments": [],
                "rules": [
                    {
                        "id": "r",
                        "effect": "allow",
                        "action": "a",
                        "resource": "b",
                        "roles": ["ghost"],
                    }
                ],
            }
        )


def test_duplicate_ids_are_refused():
    with pytest.raises(PolicyError, match="share the id"):
        parse(
            {
                "roles": {},
                "assignments": [],
                "rules": [
                    {
                        "id": "r",
                        "effect": "allow",
                        "action": "a",
                        "resource": "b",
                        "subjects": ["*"],
                    },
                    {
                        "id": "r",
                        "effect": "deny",
                        "action": "a",
                        "resource": "b",
                        "subjects": ["*"],
                    },
                ],
            }
        )


def test_an_unknown_top_level_key_is_refused():
    with pytest.raises(PolicyError, match="unknown key"):
        parse({"roles": {}, "assignments": [], "rules": [], "default": "allow"})


def test_an_unknown_effect_is_refused():
    with pytest.raises(PolicyError, match="effect must be"):
        parse(
            {
                "roles": {},
                "assignments": [],
                "rules": [
                    {
                        "id": "r",
                        "effect": "maybe",
                        "action": "a",
                        "resource": "b",
                        "subjects": ["*"],
                    }
                ],
            }
        )


def test_a_rule_naming_nobody_is_refused():
    with pytest.raises(PolicyError, match="can never match"):
        parse(
            {
                "roles": {},
                "assignments": [],
                "rules": [{"id": "r", "effect": "allow", "action": "a", "resource": "b"}],
            }
        )


def test_a_bad_scope_pattern_is_refused():
    with pytest.raises(PolicyError):
        parse(
            {
                "roles": {"v": {}},
                "assignments": [{"subject": "a", "role": "v", "scope": "project//acme"}],
                "rules": [],
            }
        )


def test_a_file_that_is_not_json_is_reported_with_its_name(tmp_path):
    broken = tmp_path / "broken.json"
    broken.write_text("{", encoding="utf-8")
    with pytest.raises(PolicyError, match=r"broken\.json"):
        load(broken)


def test_a_policy_can_be_round_tripped_through_json():
    payload = json.loads((HERE / "fixtures" / "policy.json").read_text(encoding="utf-8"))
    assert parse(payload).rules[0].id == "allow-read"
