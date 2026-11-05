"""Semantic versions, ordered the way the specification says to order them."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering

CORE = r"(?:0|[1-9][0-9]*)"
PRE = r"(?:[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)"
VERSION = re.compile(
    rf"^(?P<major>{CORE})\.(?P<minor>{CORE})\.(?P<patch>{CORE})"
    rf"(?:-(?P<pre>{PRE}))?(?:\+(?P<build>{PRE}))?$"
)
NUMERIC = re.compile(r"^[0-9]+$")


class VersionError(ValueError):
    """Raised when text is not a semantic version."""


def _check_identifiers(text: str) -> tuple[str, ...]:
    parts = tuple(text.split("."))
    if any(not part for part in parts):
        raise VersionError(f"{text!r} has an empty identifier")
    for part in parts:
        if NUMERIC.match(part) and len(part) > 1 and part.startswith("0"):
            raise VersionError(
                f"{text!r} has a numeric identifier with a leading zero ({part!r}); "
                "the specification forbids it because two spellings of one number "
                "would compare as different versions"
            )
    return parts


@total_ordering
@dataclass(frozen=True)
class Version:
    """A version whose ordering matches SemVer 2.0.0 precedence.

    Build metadata is kept for display but never compared: `1.0.0+sha.1` and
    `1.0.0+sha.2` are the SAME version, and sorting them would invent an order
    the specification does not have.
    """

    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: tuple[str, ...] = ()

    @property
    def text(self) -> str:
        core = f"{self.major}.{self.minor}.{self.patch}"
        pre = "-" + ".".join(self.prerelease) if self.prerelease else ""
        build = "+" + ".".join(self.build) if self.build else ""
        return core + pre + build

    @property
    def release(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    @property
    def is_prerelease(self) -> bool:
        return bool(self.prerelease)

    def __str__(self) -> str:
        return self.text

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return (self.major, self.minor, self.patch, self.prerelease) == (
            other.major,
            other.minor,
            other.patch,
            other.prerelease,
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        if self.release != other.release:
            return self.release < other.release
        return _precedence(self.prerelease) < _precedence(other.prerelease)

    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch, self.prerelease))


def _precedence(parts: tuple[str, ...]) -> tuple[int, tuple[tuple[int, object], ...]]:
    """A release sorts above any of its own prereleases; identifiers sort pairwise."""
    if not parts:
        return (1, ())
    ranked: list[tuple[int, object]] = []
    for part in parts:
        if NUMERIC.match(part):
            ranked.append((0, int(part)))
        else:
            ranked.append((1, part))
    return (0, tuple(ranked))


def parse(text: str) -> Version:
    match = VERSION.match(text.strip())
    if not match:
        raise VersionError(
            f"{text!r} is not a semantic version; the shape is MAJOR.MINOR.PATCH "
            "with optional -prerelease and +build"
        )
    pre = _check_identifiers(match.group("pre")) if match.group("pre") else ()
    build = _check_identifiers(match.group("build")) if match.group("build") else ()
    return Version(
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch")),
        pre,
        build,
    )


def try_parse(text: str) -> Version | None:
    try:
        return parse(text)
    except VersionError:
        return None
