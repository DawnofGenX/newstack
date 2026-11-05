"""A condition that mentions an attribute nobody sent is not satisfied.

Silently treating a missing attribute as equal to anything is how "only the owner
may edit this" turns into "anybody may edit this". Missing is reported, and the
rule does not match.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

OPERATORS = ("eq", "neq", "in", "not_in", "lt", "lte", "gt", "gte", "present", "absent")
MISSING = object()


class ConditionError(ValueError):
    """A condition that cannot be evaluated at all."""


@dataclass(frozen=True)
class Outcome:
    satisfied: bool
    reason: str


def _resolve(operand: object, subject: dict[str, str], resource: dict[str, str]) -> object:
    if not isinstance(operand, str) or not operand.startswith("$"):
        return operand
    namespace, _, name = operand[1:].partition(".")
    if namespace not in ("subject", "resource") or not name:
        raise ConditionError(f"{operand!r} is not $subject.<attr> or $resource.<attr>")
    bucket = subject if namespace == "subject" else resource
    return bucket.get(name, MISSING)


def _as_decimal(value: object, operand: object) -> Decimal:
    if isinstance(value, bool) or value is MISSING:
        raise ConditionError(f"cannot compare {operand!r} numerically")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ConditionError(f"{value!r} is not a number") from error


def evaluate(
    condition: dict[str, object] | None, subject: dict[str, str], resource: dict[str, str]
) -> Outcome:
    if not condition:
        return Outcome(True, "no condition")
    unknown = sorted(set(condition) - {"left", "op", "right"})
    if unknown:
        raise ConditionError(f"unknown condition field(s) {', '.join(unknown)}")
    op = condition.get("op")
    if op not in OPERATORS:
        raise ConditionError(f"{op!r} is not one of {', '.join(OPERATORS)}")
    if "left" not in condition:
        raise ConditionError("a condition needs a left operand")
    left = _resolve(condition["left"], subject, resource)
    if op in ("present", "absent"):
        present = left is not MISSING
        wanted = op == "present"
        if present == wanted:
            return Outcome(True, f"{condition['left']} is {'present' if present else 'absent'}")
        return Outcome(False, f"{condition['left']} is {'present' if present else 'absent'}")
    right = _resolve(condition.get("right"), subject, resource)
    if MISSING in (left, right):
        which = "left" if left is MISSING else "right"
        return Outcome(False, f"the {which} operand is missing, so this is not a match")
    if op in ("eq", "neq"):
        same = str(left) == str(right)
        return Outcome(
            same if op == "eq" else not same, f"{left!r} {'==' if op == 'eq' else '!='} {right!r}"
        )
    if op in ("in", "not_in"):
        options = right if isinstance(right, list) else str(right).split(",")
        found = any(str(candidate).strip() == str(left) for candidate in options)
        return Outcome(
            found if op == "in" else not found,
            f"{left!r} {'in' if found else 'not in'} {list(options)!r}",
        )
    left_number = _as_decimal(left, condition["left"])
    right_number = _as_decimal(right, condition.get("right"))
    result = {
        "lt": left_number < right_number,
        "lte": left_number <= right_number,
        "gt": left_number > right_number,
        "gte": left_number >= right_number,
    }[op]
    return Outcome(result, f"{left_number} {'<' if op == 'lt' else ''}{op} {right_number}")
