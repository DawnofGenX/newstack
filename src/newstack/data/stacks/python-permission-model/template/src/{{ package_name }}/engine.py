"""The engine answers allow or deny, and it can show every rule it looked at.

The order is fixed by the policy, not by the file: a matching deny always wins,
then a matching allow, then the default deny. Ties are broken by rule id so two
runs over the same file produce the same sentence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from . import conditions, patterns
from .policy import Policy, Rule


@dataclass(frozen=True)
class Request:
    subject: str
    action: str
    resource: str
    subject_attributes: Mapping[str, str] = None  # type: ignore[assignment]
    resource_attributes: Mapping[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.subject_attributes is None:
            object.__setattr__(self, "subject_attributes", {})
        if self.resource_attributes is None:
            object.__setattr__(self, "resource_attributes", {})

    def line(self) -> str:
        return f"{self.subject} wants {self.action} on {self.resource}"


@dataclass(frozen=True)
class Considered:
    rule: Rule
    matched: bool
    because: str

    def line(self) -> str:
        mark = "MATCH" if self.matched else "-"
        return f"  {mark:<5}  {self.rule.effect:<5}  {self.rule.id:<24}  {self.because}"


@dataclass(frozen=True)
class Decision:
    request: Request
    effect: str
    winner: str | None
    held: tuple[tuple[str, str | None], ...]
    considered: tuple[Considered, ...]

    @property
    def allowed(self) -> bool:
        return self.effect == "allow"

    def lines(self) -> list[str]:
        roles = ", ".join(f"{name}@{scope or '*'}" for name, scope in self.held) or "none"
        head = [
            f"request   {self.request.line()}",
            f"roles     {roles}",
        ]
        if self.effect == "allow":
            head.append(f"decision  ALLOW  by {self.winner}")
        elif self.effect == "deny":
            head.append(f"decision  DENY   by {self.winner}")
        else:
            head.append("decision  DENY   by default: no rule matched")
        body = [item.line() for item in self.considered]
        if not body:
            body = ["  (no rules were considered)"]
        return head + body

    def as_dict(self) -> dict[str, object]:
        return {
            "subject": self.request.subject,
            "action": self.request.action,
            "resource": self.request.resource,
            "effect": self.effect,
            "allowed": self.allowed,
            "winner": self.winner,
            "roles": [f"{name}@{scope or '*'}" for name, scope in self.held],
            "considered": [
                {
                    "id": item.rule.id,
                    "effect": item.rule.effect,
                    "matched": item.matched,
                    "because": item.because,
                }
                for item in self.considered
            ],
        }


def _consider(
    policy: Policy, request: Request, rule: Rule, held: tuple[tuple[str, str | None], ...]
) -> Considered:
    if not patterns.matches(rule.action, request.action, ":"):
        return Considered(rule, False, f"action {request.action} is not {rule.action}")
    if not patterns.matches(rule.resource, request.resource):
        return Considered(
            rule,
            False,
            f"resource pattern {rule.resource} does not cover {request.resource}",
        )
    if rule.roles:
        names = {name for name, _ in held}
        if not names.intersection(rule.roles):
            wanted = ", ".join(sorted(rule.roles))
            elsewhere = [
                f"{role} on {assignment.scope}"
                for assignment in policy.assignments_for(request.subject)
                for role in rule.roles
                if role in policy.chain(assignment.role)
            ]
            where = f" ({elsewhere[0]} only)" if elsewhere else ""
            return Considered(rule, False, f"holds none of the roles {wanted} here{where}")
    if rule.subjects and request.subject not in rule.subjects and "*" not in rule.subjects:
        return Considered(rule, False, f"subject {request.subject} is not named")
    outcome = conditions.evaluate(
        rule.condition, dict(request.subject_attributes), dict(request.resource_attributes)
    )
    if not outcome.satisfied:
        return Considered(rule, False, f"condition not met: {outcome.reason}")
    return Considered(rule, True, outcome.reason)


def decide(policy: Policy, request: Request) -> Decision:
    held = policy.held(request.subject, request.resource)
    considered = tuple(_consider(policy, request, rule, held) for rule in policy.rules)
    matched = [item for item in considered if item.matched]
    denies = sorted(
        (item for item in matched if item.rule.effect == "deny"), key=lambda item: item.rule.id
    )
    allows = sorted(
        (item for item in matched if item.rule.effect == "allow"), key=lambda item: item.rule.id
    )
    if denies:
        return Decision(request, "deny", denies[0].rule.id, held, considered)
    if allows:
        return Decision(request, "allow", allows[0].rule.id, held, considered)
    return Decision(request, "default", None, held, considered)
