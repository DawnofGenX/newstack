"""Resources are paths; * is one segment, ** is all the rest.

The trap this module exists to close: `project:*` does not match
`project:acme/doc:42`, because that resource has two segments after the first
separator and one `*` is one segment. People write `project:*` believing it means
"everything under project", and then an audit finds the rule never matched.
"""

from __future__ import annotations

from fnmatch import fnmatchcase


class PatternError(ValueError):
    """A pattern that cannot mean anything."""


def segments(text: str, separator: str = "/") -> list[str]:
    if not text:
        raise PatternError("a pattern cannot be empty")
    parts = text.split(separator)
    if any(part == "" for part in parts):
        raise PatternError(f"{text!r} has an empty segment")
    return parts


def _outranks(wanted: list[str], given: list[str]) -> bool:
    def walk(pattern_at: int, value_at: int) -> bool:
        if pattern_at == len(wanted):
            return value_at == len(given)
        segment = wanted[pattern_at]
        if segment == "**":
            return any(walk(pattern_at + 1, skip) for skip in range(value_at, len(given) + 1))
        if segment.endswith("**"):
            prefix = segment[:-2]
            if value_at == len(given) or not given[value_at].startswith(prefix):
                return False
            return any(walk(pattern_at + 1, skip) for skip in range(value_at + 1, len(given) + 1))
        if value_at == len(given):
            return False
        if segment == "*" or fnmatchcase(given[value_at], segment):
            return walk(pattern_at + 1, value_at + 1)
        return False

    return walk(0, 0)


def matches(pattern: str, value: str, separator: str = "/") -> bool:
    """True when the whole value is matched by the pattern.

    `*` matches inside one segment (`project:*` matches `project:acme`), a bare
    `*` matches any one segment, and `**` matches any number of segments.
    """
    wanted = segments(pattern, separator)
    given = segments(value, separator)
    return _outranks(wanted, given)


def scoped(scope: str | None, resource: str, separator: str = "/") -> bool:
    """A role assigned on `project:acme` applies to it and to everything under it."""
    if scope is None or scope == "*":
        return True
    wanted = segments(scope, separator)
    given = segments(resource, separator)
    if len(wanted) > len(given):
        return False
    for index, segment in enumerate(wanted):
        if segment == "**":
            return True
        if segment not in ("*", given[index]):
            return False
    return True


def depth(pattern: str, separator: str = "/") -> int:
    """How many segments the pattern has; ** makes the rest unbounded."""
    return len(segments(pattern, separator))
