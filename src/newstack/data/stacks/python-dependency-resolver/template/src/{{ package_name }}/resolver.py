"""Backtracking resolution, with every dead end kept as an explanation."""

from __future__ import annotations

from dataclasses import dataclass, field

from .index import Index
from .ranges import Range
from .versions import Version

YOU = "your project"
MAX_EXPLORED = 20_000


class ResolveError(RuntimeError):
    """Raised when no assignment of versions satisfies every requirement."""

    def __init__(self, message: str, conflicts: list[str]) -> None:
        super().__init__(message)
        self.conflicts = conflicts


@dataclass(frozen=True)
class Requirement:
    """One package asking for a range of another: the raw material of a conflict."""

    package: str
    constraint: Range
    parent: str

    def text(self) -> str:
        return f"{self.parent} needs {self.package} {self.constraint.text()}"


@dataclass(frozen=True)
class Choice:
    package: str
    version: Version
    because: str
    requirements: tuple[Requirement, ...]

    def line(self) -> str:
        return f"  {self.package:<18} {self.version.text:<12} {self.because}"


@dataclass
class Resolution:
    choices: dict[str, Choice]
    explored: int = 0
    requirements: dict[str, tuple[Requirement, ...]] = field(default_factory=dict)

    @property
    def count(self) -> int:
        return len(self.choices)

    def version(self, package: str) -> Version:
        return self.choices[package].version

    def lines(self) -> list[str]:
        return [self.choices[name].line() for name in sorted(self.choices)]

    def why(self, package: str) -> list[str]:
        choice = self.choices[package]
        # The requirements known at the END of the search, not at the moment of
        # the choice: a package chosen early is still constrained by everything
        # that was resolved after it, and saying less would be a half-truth.
        asked = sorted(
            {item.text() for item in self.requirements.get(package, choice.requirements)}
        )
        return [
            f"{choice.package} {choice.version.text} — {choice.because}",
            *[f"  {line}" for line in asked],
        ]

    def as_dict(self) -> dict:
        return {
            "packages": {name: self.choices[name].version.text for name in sorted(self.choices)},
            "explored": self.explored,
        }


def _allowed(index: Index, name: str, requirements: list[Requirement]) -> tuple[Version, ...]:
    published = index.candidates(name, requirements[0].constraint)
    return tuple(
        version
        for version in published
        if all(item.constraint.allows(version) for item in requirements)
    )


def _conflict(index: Index, name: str, requirements: list[Requirement]) -> str:
    lines = [f"cannot pick a version of {name}:"]
    lines.extend(f"  {item.text()}" for item in requirements)
    lines.append(f"  published: {', '.join(index.published(name))}")
    return "\n".join(lines)


def _ordered(allowed: tuple[Version, ...], locked: Version | None) -> tuple[Version, ...]:
    """The lockfile version goes first when it still fits: churn is a cost too."""
    if locked is not None and locked in allowed:
        return (locked, *(version for version in allowed if version != locked))
    return allowed


def resolve(
    index: Index,
    roots: dict[str, str],
    locked: dict[str, Version] | None = None,
    *,
    limit: int = MAX_EXPLORED,
) -> Resolution:
    """Find one version per package that satisfies every requirement.

    The search is deterministic: pending packages are visited most-constrained
    first and ties break on name, so two runs over the same index and lock
    produce the same answer regardless of the order the roots were written.
    """
    from .ranges import RangeError, parse_range

    locked = locked or {}
    requirements: dict[str, list[Requirement]] = {}
    for package, text in roots.items():
        try:
            constraint = parse_range(text)
        except RangeError as error:
            raise ResolveError(f"{package}: {error}", []) from error
        requirements.setdefault(package, []).append(Requirement(package, constraint, YOU))
    for package in requirements:
        if package not in index:
            raise ResolveError(f"{package!r} is not published in this index", [])

    explored = 0
    conflicts: list[str] = []

    def walk(chosen: dict[str, Choice], pending: dict[str, list[Requirement]]) -> Resolution | None:
        nonlocal explored
        explored += 1
        if explored > limit:
            raise ResolveError(
                f"gave up after exploring {limit} partial solutions; "
                "the index is either unsolvable or a search that needs a better heuristic",
                conflicts,
            )
        open_packages = [name for name in pending if name not in chosen]
        if not open_packages:
            return Resolution(
                dict(chosen),
                explored,
                {name: tuple(items) for name, items in pending.items()},
            )

        scored = []
        for name in sorted(open_packages):
            options = _allowed(index, name, pending[name])
            scored.append((len(options), name, options))
        _, target, options = min(scored)
        if not options:
            conflicts.append(_conflict(index, target, pending[target]))
            return None

        for version in _ordered(options, locked.get(target)):
            branch = dict(chosen)
            branch[target] = Choice(
                target,
                version,
                _because(target, version, pending[target], locked),
                tuple(pending[target]),
            )
            # Lists are copied, not shared: a branch that fails must not leak
            # its requirements into the next candidate's history.
            next_requirements = {name: list(items) for name, items in pending.items()}
            reject = None
            for dependency, constraint in index.release(target, version).dependencies:
                next_requirements.setdefault(dependency, []).append(
                    Requirement(dependency, constraint, f"{target}@{version.text}")
                )
                already = branch.get(dependency)
                if already is not None and not constraint.allows(already.version):
                    wanted = ", ".join(
                        sorted({item.constraint.text() for item in already.requirements})
                    )
                    reject = (
                        f"{target}@{version.text} needs {dependency} {constraint.text()}, "
                        f"but {dependency} {already.version.text} was already chosen for {wanted}"
                    )
                    break
            if reject is not None:
                conflicts.append(reject)
                continue
            found = walk(branch, next_requirements)
            if found is not None:
                return found
        return None

    found = walk({}, requirements)
    if found is None:
        raise ResolveError(_summary(conflicts), _dedupe(conflicts))
    return found


def _because(
    package: str, version: Version, requirements: list[Requirement], locked: dict[str, Version]
) -> str:
    if locked.get(package) == version:
        return "kept from the lock"
    if not requirements:
        return "no constraint"
    if version.is_prerelease:
        return "the only range that asked for a prerelease"
    return "highest version that satisfies every range"


def _dedupe(conflicts: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for item in conflicts:
        seen.setdefault(item, None)
    return list(seen)


def _summary(conflicts: list[str]) -> str:
    if not conflicts:
        return "no resolution exists"
    unique = _dedupe(conflicts)
    shown = unique[:3]
    body = "\n\n".join(shown)
    extra = "" if len(unique) <= 3 else f"\n\n({len(unique) - 3} more dead end(s) recorded)"
    return (
        "no resolution exists. The search proved it by exhausting these dead ends:"
        f"\n\n{body}{extra}"
    )
