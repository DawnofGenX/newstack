"""Checks the claims in the README against the code, without a policy file."""

from __future__ import annotations

import sys

from . import conditions, patterns
from .engine import Request, decide
from .policy import PolicyError, parse

FAILED: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"ok   {name}")
    else:
        print(f"FAIL {name} {detail}".rstrip())
        FAILED.append(name)


def refuses(name: str, function, text: str) -> None:
    try:
        function()
    except PolicyError as error:
        check(name, text in str(error), f"(got {str(error)!r})")
    else:
        check(name, False, "(no error raised)")


def main() -> int:
    check("one star is one segment", not patterns.matches("project:*", "project:acme/doc:42"))
    check("two stars reach the bottom", patterns.matches("project:**", "project:acme/doc:42"))
    check("a literal path matches", patterns.matches("project:acme/*", "project:acme/doc:42"))
    check("paths are case sensitive", not patterns.matches("Project:acme", "project:acme"))
    check("scope covers children", patterns.scoped("project:acme", "project:acme/doc:42"))
    check(
        "scope does not cover siblings", not patterns.scoped("project:acme", "project:other/doc:42")
    )
    check(
        "an empty pattern is refused",
        _raises(lambda: patterns.segments("a//b"), patterns.PatternError),
    )

    ok = conditions.evaluate(
        {"left": "$resource.owner", "op": "eq", "right": "$subject.id"},
        {"id": "bob"},
        {"owner": "bob"},
    )
    check("a condition that holds is satisfied", ok.satisfied, ok.reason)
    missing = conditions.evaluate(
        {"left": "$resource.owner", "op": "eq", "right": "$subject.id"}, {"id": "bob"}, {}
    )
    check("a missing attribute is not a match", not missing.satisfied, missing.reason)
    check("missing is reported", "missing" in missing.reason, missing.reason)
    listed = conditions.evaluate(
        {"left": "$subject.id", "op": "in", "right": ["a", "b"]}, {"id": "b"}, {}
    )
    check("in matches a list", listed.satisfied, listed.reason)

    policy = parse(_DEMO)
    check("a role inherits transitively", policy.chain("editor") == ("editor", "viewer"))
    check("the chain is stable", policy.chain("editor") == policy.chain("editor"))
    decides = decide(policy, Request("alice", "docs:write", "project:acme/doc:42"))
    check("the inherited role allows the write", decides.allowed, decides.effect)
    check("the winner is named", decides.winner == "allow-write", str(decides.winner))
    denied = decide(policy, Request("alice", "docs:read", "project:acme/secret"))
    check("a deny outranks an allow", denied.effect == "deny", denied.effect)
    check("the deny is the winner", denied.winner == "deny-secret", str(denied.winner))
    outside = decide(policy, Request("alice", "docs:write", "project:other/doc:1"))
    check("a scoped role does not follow the subject", outside.effect == "default", outside.effect)
    check(
        "the scope is explained",
        any("holds none of the roles editor" in item.because for item in outside.considered),
    )
    unnamed = decide(policy, Request("dave", "docs:read", "project:acme/doc:1"))
    check("an unassigned subject is denied by default", unnamed.effect == "default", unnamed.effect)
    owner = decide(
        policy,
        Request(
            "bob",
            "comments:create",
            "project:acme/doc:7",
            subject_attributes={"id": "bob"},
            resource_attributes={"owner": "bob"},
        ),
    )
    check("a condition can grant", owner.allowed, owner.effect)
    not_owner = decide(
        policy,
        Request(
            "bob",
            "comments:create",
            "project:acme/doc:7",
            subject_attributes={"id": "bob"},
            resource_attributes={"owner": "dave"},
        ),
    )
    check("a false condition does not grant", not_owner.effect == "default", not_owner.effect)
    check(
        "every rule is listed in the trace",
        len(not_owner.considered) == len(policy.rules),
        str(len(not_owner.considered)),
    )
    check(
        "the trace is deterministic",
        [item.line() for item in not_owner.considered]
        == [item.line() for item in decide(policy, not_owner.request).considered],
    )

    refuses(
        "a cycle is refused",
        lambda: parse(
            {
                "roles": {"a": {"inherits": ["b"]}, "b": {"inherits": ["a"]}},
                "assignments": [],
                "rules": [],
            }
        ),
        "inherits itself",
    )
    refuses(
        "an unknown role in an assignment is refused",
        lambda: parse(
            {"roles": {}, "assignments": [{"subject": "x", "role": "ghost"}], "rules": []}
        ),
        "unknown role",
    )
    refuses(
        "a duplicate rule id is refused",
        lambda: parse(
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
        ),
        "share the id",
    )
    refuses(
        "a rule that names nobody is refused",
        lambda: parse(
            {
                "roles": {},
                "assignments": [],
                "rules": [{"id": "r", "effect": "allow", "action": "a", "resource": "b"}],
            }
        ),
        "can never match",
    )
    refuses(
        "an unknown operator is refused",
        lambda: parse(
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
                        "condition": {"left": "x", "op": "approximately", "right": "y"},
                    }
                ],
            }
        ),
        "not a known operator",
    )
    refuses(
        "an unknown effect is refused",
        lambda: parse(
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
        ),
        "effect must be",
    )

    if FAILED:
        print(f"selftest: {len(FAILED)} check(s) failed")
        return 1
    print("selftest: all checks passed")
    return 0


def _raises(function, kind) -> bool:
    try:
        function()
    except kind:
        return True
    return False


_DEMO = {
    "roles": {"viewer": {}, "editor": {"inherits": ["viewer"]}},
    "assignments": [
        {"subject": "alice", "role": "editor", "scope": "project:acme"},
        {"subject": "bob", "role": "viewer"},
    ],
    "rules": [
        {
            "id": "allow-read",
            "effect": "allow",
            "action": "docs:read",
            "resource": "project:**",
            "roles": ["viewer"],
        },
        {
            "id": "allow-write",
            "effect": "allow",
            "action": "docs:write",
            "resource": "project:**",
            "roles": ["editor"],
        },
        {
            "id": "allow-comment",
            "effect": "allow",
            "action": "comments:create",
            "resource": "project:**",
            "roles": ["viewer"],
            "condition": {"left": "$resource.owner", "op": "eq", "right": "$subject.id"},
        },
        {
            "id": "deny-secret",
            "effect": "deny",
            "action": "docs:*",
            "resource": "**/secret",
            "subjects": ["*"],
        },
    ],
}

if __name__ == "__main__":
    sys.exit(main())
