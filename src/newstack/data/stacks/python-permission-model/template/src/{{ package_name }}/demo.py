"""Six decisions that show what the engine does when a rule disagrees with itself."""

from __future__ import annotations

from . import patterns
from .engine import Request, decide
from .policy import parse

DEMO_POLICY = parse(
    {
        "roles": {
            "viewer": {},
            "editor": {"inherits": ["viewer"]},
            "admin": {"inherits": ["editor"]},
        },
        "assignments": [
            {"subject": "alice", "role": "editor", "scope": "project:acme"},
            {"subject": "carol", "role": "viewer"},
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
)


def _case(title: str, request: Request) -> None:
    print()
    print(title)
    for line in decide(DEMO_POLICY, request).lines():
        print(line)


def main() -> int:
    print("policy: editor inherits viewer, alice is editor on project:acme only,")
    print("        one rule requires the resource owner, one deny covers any secret")
    print()
    print("wildcard check")
    print(
        f"  project:*              matches project:acme/doc:42  "
        f"{patterns.matches('project:*', 'project:acme/doc:42')}"
    )
    print(
        f"  project:acme/*         matches project:acme/doc:42  "
        f"{patterns.matches('project:acme/*', 'project:acme/doc:42')}"
    )
    print(
        f"  project:**             matches project:acme/doc:42  "
        f"{patterns.matches('project:**', 'project:acme/doc:42')}"
    )
    _case(
        "1. alice writes a document inside her scope",
        Request("alice", "docs:write", "project:acme/doc:42"),
    )
    _case(
        "2. carol, a viewer, tries the same write",
        Request("carol", "docs:write", "project:acme/doc:42"),
    )
    _case(
        "3. alice reads a document named secret: the deny outranks the allow",
        Request("alice", "docs:read", "project:acme/secret"),
    )
    _case(
        "4. alice writes outside her scope: the role does not follow her",
        Request("alice", "docs:write", "project:other/doc:1"),
    )
    _case(
        "5. bob comments on his own document",
        Request(
            "bob",
            "comments:create",
            "project:acme/doc:7",
            subject_attributes={"id": "bob"},
            resource_attributes={"owner": "bob"},
        ),
    )
    _case(
        "6. the same comment, with the owner attribute missing",
        Request("bob", "comments:create", "project:acme/doc:7", subject_attributes={"id": "bob"}),
    )
    print()
    print("note: case 6 is the whole point. A condition that cannot be evaluated is")
    print("      not a match, so the request falls through to the default deny.")
    return 0
