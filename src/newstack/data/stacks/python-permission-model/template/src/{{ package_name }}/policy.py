"""A policy file is data, and data gets validated before it decides anything."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from . import patterns
from .conditions import OPERATORS

EFFECTS = ("allow", "deny")


class PolicyError(ValueError):
    """A policy that cannot be trusted to answer."""


@dataclass(frozen=True)
class Role:
    name: str
    inherits: tuple[str, ...] = ()


@dataclass(frozen=True)
class Assignment:
    subject: str
    role: str
    scope: str | None = None

    def line(self) -> str:
        return f"{self.role} on {self.scope or '*'}"


@dataclass(frozen=True)
class Rule:
    id: str
    effect: str
    action: str
    resource: str
    roles: tuple[str, ...] = ()
    subjects: tuple[str, ...] = ()
    condition: dict[str, object] | None = None

    def line(self) -> str:
        who = ", ".join(self.roles) if self.roles else ", ".join(self.subjects)
        return f"{self.effect} {self.id}: {self.action} on {self.resource} for {who}"


@dataclass(frozen=True)
class Policy:
    roles: dict[str, Role]
    assignments: tuple[Assignment, ...]
    rules: tuple[Rule, ...]

    def chain(self, name: str, seen: tuple[str, ...] = ()) -> tuple[str, ...]:
        """The role and everything it inherits, in breadth-first order."""
        if name in seen:
            raise PolicyError(
                f"role {name} inherits itself through {' -> '.join((*seen, name))}; "
                "a cycle has no fixed point, so it has no answer"
            )
        role = self.roles.get(name)
        if role is None:
            raise PolicyError(f"unknown role {name!r}")
        found: list[str] = [name]
        for parent in role.inherits:
            for inherited in self.chain(parent, (*seen, name)):
                if inherited not in found:
                    found.append(inherited)
        return tuple(found)

    def assignments_for(self, subject: str) -> tuple[Assignment, ...]:
        return tuple(
            assignment for assignment in self.assignments if assignment.subject in (subject, "*")
        )

    def held(self, subject: str, resource: str) -> tuple[tuple[str, str | None], ...]:
        """Every (role, scope) the subject holds that applies to this resource."""
        held: list[tuple[str, str | None]] = []
        for assignment in self.assignments_for(subject):
            if patterns.scoped(assignment.scope, resource):
                for name in self.chain(assignment.role):
                    if (name, assignment.scope) not in held:
                        held.append((name, assignment.scope))
        return tuple(held)

    def validate(self) -> None:
        for name in self.roles:
            self.chain(name)
        for assignment in self.assignments:
            if assignment.role not in self.roles:
                raise PolicyError(
                    f"assignment for {assignment.subject!r} names unknown role {assignment.role!r}"
                )
            if not assignment.subject:
                raise PolicyError("an assignment needs a subject")
            if assignment.scope is not None:
                try:
                    patterns.segments(assignment.scope)
                except patterns.PatternError as error:
                    raise PolicyError(f"assignment for {assignment.subject!r}: {error}") from error
        seen: set[str] = set()
        for rule in self.rules:
            if not rule.id:
                raise PolicyError("every rule needs an id, or no audit log can name it")
            if rule.id in seen:
                raise PolicyError(f"two rules share the id {rule.id!r}")
            seen.add(rule.id)
            if rule.effect not in EFFECTS:
                raise PolicyError(
                    f"rule {rule.id}: effect must be allow or deny, got {rule.effect!r}"
                )
            try:
                patterns.segments(rule.action, ":")
                patterns.segments(rule.resource)
            except patterns.PatternError as error:
                raise PolicyError(f"rule {rule.id}: {error}") from error
            if not rule.roles and not rule.subjects:
                raise PolicyError(
                    f"rule {rule.id}: names no role and no subject, so it can never match"
                )
            for role in rule.roles:
                if role not in self.roles:
                    raise PolicyError(f"rule {rule.id}: unknown role {role!r}")
            if rule.condition:
                unknown = sorted(set(rule.condition) - {"left", "op", "right"})
                if unknown:
                    raise PolicyError(
                        f"rule {rule.id}: unknown condition field(s) {', '.join(unknown)}"
                    )
                if rule.condition.get("op") not in OPERATORS:
                    raise PolicyError(
                        f"rule {rule.id}: {rule.condition.get('op')!r} is not a known operator"
                    )


def _strings(value: object, where: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PolicyError(f"{where} must be a list of strings")
    return tuple(value)


def load(path: Path | str) -> Policy:
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except OSError as error:
        raise PolicyError(f"cannot read {source}: {error}") from error
    except json.JSONDecodeError as error:
        raise PolicyError(f"{source} is not JSON: {error}") from error
    try:
        return parse(payload)
    except PolicyError as error:
        raise PolicyError(f"{source}: {error}") from error


def parse(payload: object) -> Policy:
    if not isinstance(payload, dict):
        raise PolicyError("a policy must be an object")
    unknown = sorted(set(payload) - {"roles", "assignments", "rules"})
    if unknown:
        raise PolicyError(f"unknown key(s) {', '.join(unknown)}")
    roles: dict[str, Role] = {}
    raw_roles = payload.get("roles", {})
    if not isinstance(raw_roles, dict):
        raise PolicyError("roles must be an object of name -> role")
    for name, body in raw_roles.items():
        if not isinstance(body, dict):
            raise PolicyError(f"role {name!r} must be an object")
        unknown_role = sorted(set(body) - {"inherits"})
        if unknown_role:
            raise PolicyError(f"role {name!r}: unknown key(s) {', '.join(unknown_role)}")
        roles[name] = Role(name, _strings(body.get("inherits"), f"role {name!r} inherits"))
    assignments: list[Assignment] = []
    for index, body in enumerate(payload.get("assignments", [])):
        if not isinstance(body, dict):
            raise PolicyError(f"assignment {index} must be an object")
        unknown_assignment = sorted(set(body) - {"subject", "role", "scope"})
        if unknown_assignment:
            raise PolicyError(f"assignment {index}: unknown key(s) {', '.join(unknown_assignment)}")
        for required in ("subject", "role"):
            if not isinstance(body.get(required), str) or not body[required]:
                raise PolicyError(f"assignment {index}: {required} must be a non-empty string")
        scope = body.get("scope")
        if scope is not None and not isinstance(scope, str):
            raise PolicyError(f"assignment {index}: scope must be a string when given")
        assignments.append(Assignment(body["subject"], body["role"], scope))
    rules: list[Rule] = []
    for index, body in enumerate(payload.get("rules", [])):
        if not isinstance(body, dict):
            raise PolicyError(f"rule {index} must be an object")
        unknown_rule = sorted(
            set(body) - {"id", "effect", "action", "resource", "roles", "subjects", "condition"}
        )
        if unknown_rule:
            raise PolicyError(f"rule {index}: unknown key(s) {', '.join(unknown_rule)}")
        for required in ("id", "effect", "action", "resource"):
            if not isinstance(body.get(required), str) or not body[required]:
                raise PolicyError(f"rule {index}: {required} must be a non-empty string")
        condition = body.get("condition")
        if condition is not None and not isinstance(condition, dict):
            raise PolicyError(f"rule {body['id']}: condition must be an object")
        rules.append(
            Rule(
                id=body["id"],
                effect=body["effect"],
                action=body["action"],
                resource=body["resource"],
                roles=_strings(body.get("roles"), f"rule {body['id']} roles"),
                subjects=_strings(body.get("subjects"), f"rule {body['id']} subjects"),
                condition=condition,
            )
        )
    policy = Policy(roles, tuple(assignments), tuple(rules))
    policy.validate()
    return policy


def dump(policy: Policy) -> dict[str, object]:
    return {
        "roles": {name: {"inherits": list(role.inherits)} for name, role in policy.roles.items()},
        "assignments": [
            {"subject": a.subject, "role": a.role, "scope": a.scope} for a in policy.assignments
        ],
        "rules": [
            {
                "id": r.id,
                "effect": r.effect,
                "action": r.action,
                "resource": r.resource,
                "roles": list(r.roles),
                "subjects": list(r.subjects),
                "condition": r.condition,
            }
            for r in policy.rules
        ],
    }
