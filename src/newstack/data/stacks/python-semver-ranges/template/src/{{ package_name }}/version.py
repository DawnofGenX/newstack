"""A version is ordered fields, not a decimal number."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering

PATTERN = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:-(?P<prerelease>[0-9A-Za-z.-]+))?"
    r"(?:\+(?P<build>[0-9A-Za-z.-]+))?$"
)
NUMERIC = re.compile(r"^(?:0|[1-9]\d*)$")


class VersionError(ValueError):
    """A string that is not a version, or a comparison with no answer."""


def _prerelease_key(identifiers: tuple[str, ...]) -> tuple[tuple[int, object], ...]:
    return tuple((0, int(item)) if item.isdigit() else (1, item) for item in identifiers)


@total_ordering
@dataclass(frozen=True, eq=False)
class Version:
    """One version. Precedence follows the spec: build metadata is ignored."""

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: str = ""

    @property
    def core(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    @property
    def is_prerelease(self) -> bool:
        return bool(self.prerelease)

    @property
    def precedence(self) -> tuple[object, ...]:
        if not self.prerelease:
            return (self.major, self.minor, self.patch, ((2, ""),))
        return (self.major, self.minor, self.patch, _prerelease_key(self.prerelease))

    def __str__(self) -> str:
        text = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            text += "-" + ".".join(self.prerelease)
        if self.build:
            text += "+" + self.build
        return text

    def __repr__(self) -> str:
        return f"Version({str(self)!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self.precedence == other.precedence

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self.precedence < other.precedence

    def __hash__(self) -> int:
        return hash(self.precedence)


def parse(text: str) -> Version:
    """Read a strict semver string. Leading zeros are refused, not repaired."""
    cleaned = text.strip()
    match = PATTERN.match(cleaned)
    if match is None:
        raise VersionError(
            f"{cleaned!r} is not a version: it needs major.minor.patch, "
            "and the numeric fields are decimal"
        )
    fields = (match.group("major"), match.group("minor"), match.group("patch"))
    for name, field in zip(("major", "minor", "patch"), fields, strict=True):
        if not NUMERIC.match(field):
            raise VersionError(
                f"{cleaned!r} has a leading zero in its {name} field; "
                "1.02.3 is not 1.2.3, and this parser will not guess"
            )
    raw_prerelease = match.group("prerelease") or ""
    identifiers = tuple(raw_prerelease.split(".")) if raw_prerelease else ()
    for identifier in identifiers:
        if identifier.isdigit() and not NUMERIC.match(identifier):
            raise VersionError(
                f"{cleaned!r} has a numeric prerelease identifier with a leading zero"
            )
    return Version(
        major=int(fields[0]),
        minor=int(fields[1]),
        patch=int(fields[2]),
        prerelease=identifiers,
        build=match.group("build") or "",
    )


def compare(left: Version, right: Version) -> int:
    if left < right:
        return -1
    if right < left:
        return 1
    return 0


def version_at(major: int, minor: int = 0, patch: int = 0) -> Version:
    return Version(major, minor, patch)
