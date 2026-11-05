"""Version ranges and the four rules people get wrong about them."""

from __future__ import annotations

from dataclasses import dataclass

from .versions import Version, VersionError, parse


class RangeError(ValueError):
    """Raised when a range cannot be parsed."""


ORDER = {"<": 0, "<=": 1, ">": 2, ">=": 3, "=": 4}


@dataclass(frozen=True)
class Comparator:
    """One operator and one version. `=` exists so 1.2.3 can be written bare."""

    op: str
    version: Version

    def allows(self, candidate: Version) -> bool:
        if self.op == "=":
            return candidate == self.version
        if self.op == "<":
            return candidate < self.version
        if self.op == "<=":
            return candidate <= self.version
        if self.op == ">":
            return candidate > self.version
        return candidate >= self.version

    def text(self) -> str:
        return f"{self.op}{self.version.text}"


@dataclass(frozen=True)
class Range:
    """A conjunction of comparators, optionally unioned by `||`.

    An empty `alternatives` entry means "any release": `*` must not match a
    prerelease, because no released version was ever asked for.
    """

    alternatives: tuple[tuple[Comparator, ...], ...] = ((),)
    source: str = "*"

    def allows(self, candidate: Version) -> bool:
        for comparators in self.alternatives:
            if not all(item.allows(candidate) for item in comparators):
                continue
            if candidate.is_prerelease and not self._opts_into_prerelease(candidate, comparators):
                continue
            return True
        return False

    @staticmethod
    def _opts_into_prerelease(candidate: Version, comparators: tuple[Comparator, ...]) -> bool:
        """A prerelease needs a comparator that names a prerelease of the same release.

        `^2.0.0` has the bound `<3.0.0`, and `3.0.0-rc.1 < 3.0.0` is true, so the
        bound alone would smuggle a release candidate into a stable range. The
        comparator must itself mention a prerelease: wanting 3.x is not wanting
        to run 3.0.0 before it exists.
        """
        return any(
            item.version.is_prerelease and item.version.release == candidate.release
            for item in comparators
        )

    def any_version(self) -> bool:
        return any(not comparators for comparators in self.alternatives)

    def text(self) -> str:
        return self.source

    def describe(self) -> str:
        if self.any_version():
            return "any version"
        return " || ".join(
            " ".join(item.text() for item in comparators) for comparators in self.alternatives
        )

    def __str__(self) -> str:
        return self.source


def _bump(version: Version, part: str) -> Version:
    if part == "major":
        return Version(version.major + 1, 0, 0)
    if part == "minor":
        return Version(version.major, version.minor + 1, 0)
    return Version(version.major, version.minor, version.patch + 1)


def _components(text: str) -> int:
    """How many of MAJOR.MINOR.PATCH the author actually wrote."""
    return len([piece for piece in text.strip().split(".") if piece != ""])


def _caret(version: Version, count: int) -> tuple[Comparator, ...]:
    """^1.2.3 allows 1.x.y, but ^0.2.3 allows only 0.2.x and ^0.0.3 only 0.0.3.

    A zero major means the API is not stable, so the leftmost non-zero part is
    the one that must not move. A bare ^0 means "anything before 1.0.0", which
    is the npm reading and the only one that makes the caret monotone.
    """
    if version.major > 0 or count == 1:
        upper = _bump(version, "major")
    elif version.minor > 0:
        upper = _bump(version, "minor")
    else:
        upper = _bump(version, "patch")
    return (Comparator(">=", version), Comparator("<", upper))


def _tilde(version: Version, count: int) -> tuple[Comparator, ...]:
    """~1.2.3 allows patch updates, ~1.2 allows 1.2.x and ~1 allows 1.x.

    The tilde freezes everything above the last component the author named.
    """
    upper = _bump(version, "major" if count == 1 else "minor")
    return (Comparator(">=", version), Comparator("<", upper))


def expand(text: str) -> tuple[Comparator, ...]:
    body = text.strip()
    if body in {"", "*", "x", "X", "latest"}:
        return ()
    for prefix, builder in (("^", _caret), ("~", _tilde)):
        if body.startswith(prefix):
            written = body[len(prefix) :]
            return builder(_need_version(written, text), _components(written))

    parts = body.replace(",", " ").split()
    comparators: list[Comparator] = []
    for part in parts:
        op = "="
        for candidate in (">=", "<=", ">", "<", "="):
            if part.startswith(candidate):
                op = candidate
                part = part[len(candidate) :]
                break
        if part in {"*", "x", "X"}:
            if op not in {"=", ">="}:
                raise RangeError(
                    f"{text!r} combines {op} with a wildcard, which no version satisfies"
                )
            continue
        comparators.append(Comparator(op, _need_version(part, text)))
    if not comparators:
        return ()
    return tuple(sorted(comparators, key=lambda item: (ORDER[item.op], item.version)))


def _need_version(text: str, whole: str) -> Version:
    padded = text.strip()
    pieces = padded.split(".")
    while len(pieces) < 3:
        pieces.append("0")
    try:
        return parse(".".join(pieces))
    except VersionError as error:
        raise RangeError(f"{whole!r} is not a range I can read: {error}") from error


def parse_range(text: str) -> Range:
    if not text or not text.strip():
        raise RangeError("an empty range is ambiguous; write * to mean any release")
    alternatives = tuple(expand(part) for part in text.split("||"))
    return Range(alternatives=alternatives, source=text.strip())
