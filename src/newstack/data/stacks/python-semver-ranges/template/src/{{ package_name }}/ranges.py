"""A range is a union of intervals, and a prerelease is opt-in."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .version import Version

OPERATORS = (">=", "<=", ">", "<", "=", "^", "~")
WILDCARDS = ("x", "X", "*")
HYPHEN = re.compile(r"\s+-\s+")


class RangeError(ValueError):
    """A range that cannot be read as a union of intervals."""


def _fill(fields: list[int]) -> Version:
    return Version(
        major=fields[0] if len(fields) > 0 else 0,
        minor=fields[1] if len(fields) > 1 else 0,
        patch=fields[2] if len(fields) > 2 else 0,
    )


def _lowest(fields: list[int], prerelease: tuple[str, ...] = ()) -> Version:
    base = _fill(fields)
    return Version(base.major, base.minor, base.patch, prerelease)


def _next_interval(fields: list[int]) -> Version | None:
    """The exclusive upper bound of the interval a partial version names."""
    if not fields:
        return None
    bumped = [*fields[:-1], fields[-1] + 1]
    return _fill(bumped)


@dataclass(frozen=True)
class Arm:
    """One conjunction of bounds: an interval, plus the prereleases it opts into."""

    lower: Version | None
    lower_inclusive: bool
    upper: Version | None
    upper_inclusive: bool
    prerelease_cores: tuple[tuple[int, int, int], ...] = ()
    text: str = ""
    empty: bool = False

    def in_bounds(self, version: Version) -> bool:
        if self.empty:
            return False
        if self.lower is not None:
            if version < self.lower:
                return False
            if version == self.lower and not self.lower_inclusive:
                return False
        if self.upper is not None:
            if self.upper < version:
                return False
            if version == self.upper and not self.upper_inclusive:
                return False
        return True

    def contains(self, version: Version) -> bool:
        if not self.in_bounds(version):
            return False
        if not version.is_prerelease:
            return True
        return version.core in self.prerelease_cores

    def bound_text(self) -> str:
        if self.empty:
            return "never"
        if self.lower is None and self.upper is None:
            return "*"
        if self.upper is None:
            return f"{'>=' if self.lower_inclusive else '>'}{self.lower}"
        if self.lower is None:
            return f"{'<=' if self.upper_inclusive else '<'}{self.upper}"
        left = "[" if self.lower_inclusive else "("
        right = "]" if self.upper_inclusive else ")"
        return f"{left}{self.lower}, {self.upper}{right}"

    def prerelease_text(self) -> str:
        return ", ".join(".".join(str(part) for part in core) for core in self.prerelease_cores)

    def render(self) -> str:
        if not self.prerelease_cores:
            return self.bound_text()
        return f"{self.bound_text()} (prerelease of {self.prerelease_text()})"


@dataclass(frozen=True)
class Range:
    arms: tuple[Arm, ...]
    text: str = ""

    def match(self, version: Version) -> int | None:
        """The one-based number of the first arm that contains the version."""
        for number, arm in enumerate(self.arms, start=1):
            if arm.contains(version):
                return number
        return None

    def allows(self, version: Version) -> bool:
        return self.match(version) is not None

    def render(self) -> str:
        return " || ".join(arm.render() for arm in self.arms)

    def prerelease_cores(self) -> tuple[tuple[int, int, int], ...]:
        cores: list[tuple[int, int, int]] = []
        for arm in self.arms:
            for core in arm.prerelease_cores:
                if core not in cores:
                    cores.append(core)
        return tuple(cores)


def _parse_partial(text: str) -> tuple[list[int], tuple[str, ...]]:
    body, _, rest = text.partition("-")
    prerelease = tuple(item for item in rest.split(".") if item)
    if body in ("", *WILDCARDS):
        return [], prerelease
    fields: list[int] = []
    for piece in body.split("."):
        if piece in WILDCARDS:
            break
        if not piece.isdigit():
            raise RangeError(
                f"{text!r} is not a version or a partial version: "
                "each field is a decimal number, x, X, or *"
            )
        fields.append(int(piece))
    if len(fields) > 3:
        raise RangeError(f"{text!r} has more than three numeric fields")
    if fields and prerelease and len(fields) < 3:
        raise RangeError(
            f"{text!r} names a prerelease without a patch version; "
            "a prerelease belongs to one exact major.minor.patch"
        )
    return fields, prerelease


def _caret_upper(fields: list[int]) -> Version | None:
    for index, value in enumerate(fields):
        if value != 0:
            return _fill([*fields[:index], value + 1, *([0] * (len(fields) - index - 1))])
    if not fields:
        return None
    return _fill([*fields[:-1], fields[-1] + 1])


def _tilde_upper(fields: list[int]) -> Version | None:
    if not fields:
        return None
    if len(fields) == 1:
        return _fill([fields[0] + 1, 0, 0])
    return _fill([fields[0], fields[1] + 1, 0])


def _arm(
    *,
    lower: Version | None,
    lower_inclusive: bool = True,
    upper: Version | None = None,
    upper_inclusive: bool = False,
    cores: tuple[tuple[int, int, int], ...] = (),
    text: str = "",
) -> Arm:
    empty = False
    if lower is not None and upper is not None:
        collided = upper < lower or (upper == lower and not (lower_inclusive and upper_inclusive))
        empty = collided
    return Arm(lower, lower_inclusive, upper, upper_inclusive, cores, text, empty)


def _token_bounds(token: str) -> Arm:
    operator = ""
    rest = token
    for candidate in OPERATORS:
        if token.startswith(candidate):
            operator, rest = candidate, token[len(candidate) :]
            break
    if rest in ("", "-", "+") and operator == "":
        raise RangeError(f"{token!r} is not a version or a bound on one")
    fields, prerelease = _parse_partial(rest)
    cores: tuple[tuple[int, int, int], ...] = ()
    exact = len(fields) == 3
    version = _lowest(fields, prerelease) if fields else None
    if prerelease:
        cores = (version.core,) if version is not None else ()

    if not fields:
        if operator in (">", "<"):
            raise RangeError(
                f"{token!r} has a bound but no version; a bound without a version has no direction"
            )
        return _arm(lower=None, text=token)

    assert version is not None
    if operator in ("", "="):
        if exact:
            return _arm(
                lower=version,
                upper=version,
                upper_inclusive=True,
                cores=cores,
                text=token,
            )
        return _arm(lower=version, upper=_next_interval(fields), cores=cores, text=token)
    if operator == ">":
        if exact:
            return _arm(lower=version, lower_inclusive=False, cores=cores, text=token)
        following = _next_interval(fields)
        return _arm(lower=following, cores=cores, text=token)
    if operator == ">=":
        return _arm(lower=version, cores=cores, text=token)
    if operator == "<":
        return _arm(lower=None, upper=version, upper_inclusive=False, cores=cores, text=token)
    if operator == "<=":
        if exact:
            return _arm(lower=None, upper=version, upper_inclusive=True, cores=cores, text=token)
        return _arm(lower=None, upper=_next_interval(fields), cores=cores, text=token)
    if operator == "^":
        return _arm(lower=version, upper=_caret_upper(fields), cores=cores, text=token)
    if operator == "~":
        return _arm(lower=version, upper=_tilde_upper(fields), cores=cores, text=token)
    raise RangeError(f"{token!r} starts with an operator this parser does not know")


def _hyphen_bounds(text: str) -> Arm:
    parts = HYPHEN.split(text)
    if len(parts) != 2:
        raise RangeError(f"{text!r} is not one hyphen range: write 'LOW - HIGH'")
    low_fields, low_pre = _parse_partial(parts[0])
    high_fields, high_pre = _parse_partial(parts[1])
    if not high_fields:
        raise RangeError(f"{text!r} has no version on the right of the hyphen")
    if not low_fields:
        raise RangeError(f"{text!r} has no version on the left of the hyphen")
    lower, lower_inc = _lowest(low_fields, low_pre), True
    cores: list[tuple[int, int, int]] = []
    if low_pre and lower is not None:
        cores.append(lower.core)
    if not high_fields:
        upper, upper_inc = None, False
    elif len(high_fields) == 3:
        upper, upper_inc = _lowest(high_fields, high_pre), True
        if high_pre:
            cores.append(upper.core)
    else:
        upper, upper_inc = _next_interval(high_fields), False
    return _arm(
        lower=lower,
        lower_inclusive=lower_inc,
        upper=upper,
        upper_inclusive=upper_inc,
        cores=tuple(cores),
        text=text,
    )


def _and(arms: list[Arm]) -> Arm:
    lower: Version | None = None
    lower_inclusive = True
    upper: Version | None = None
    upper_inclusive = True
    cores: list[tuple[int, int, int]] = []
    for arm in arms:
        if arm.empty:
            return arm
        if arm.lower is not None:
            if lower is None or arm.lower > lower:
                lower, lower_inclusive = arm.lower, arm.lower_inclusive
            elif arm.lower == lower:
                lower_inclusive = lower_inclusive and arm.lower_inclusive
        if arm.upper is not None:
            if upper is None or arm.upper < upper:
                upper, upper_inclusive = arm.upper, arm.upper_inclusive
            elif arm.upper == upper:
                upper_inclusive = upper_inclusive and arm.upper_inclusive
        for core in arm.prerelease_cores:
            if core not in cores:
                cores.append(core)
    return _arm(
        lower=lower,
        lower_inclusive=lower_inclusive,
        upper=upper,
        upper_inclusive=upper_inclusive,
        cores=tuple(cores),
        text=" ".join(arm.text for arm in arms),
    )


def parse_range(text: str) -> Range:
    cleaned = text.strip()
    if not cleaned:
        raise RangeError("an empty range has no arms; write * if you mean every version")
    arms: list[Arm] = []
    for piece in cleaned.split("||"):
        body = piece.strip()
        if not body:
            raise RangeError(
                f"{cleaned!r} has an empty arm beside '||'; an empty arm matches "
                "nothing, so this parser refuses to guess whether you meant *"
            )
        if HYPHEN.search(body):
            arms.append(_hyphen_bounds(body))
            continue
        bounds = [_token_bounds(token) for token in body.split()]
        arms.append(_and(bounds))
    return Range(tuple(arms), cleaned)


def intersect(left: Range, right: Range) -> Range | None:
    """The versions both ranges allow, or None when no version can."""
    arms: list[Arm] = []
    for first in left.arms:
        for second in right.arms:
            combined = _and([first, second])
            if not combined.empty:
                arms.append(combined)
    if not arms:
        return None
    return Range(tuple(arms), f"{left.text} && {right.text}")
