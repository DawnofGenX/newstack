"""The published packages a resolver is allowed to choose from."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .ranges import Range, RangeError, parse_range
from .versions import Version, VersionError, parse


class IndexError_(ValueError):
    """Raised when a package index is not usable."""


@dataclass(frozen=True)
class Release:
    """One published version and the ranges it demands of its dependencies."""

    version: Version
    dependencies: tuple[tuple[str, Range], ...] = ()

    def range_for(self, name: str) -> Range | None:
        for dependency, constraint in self.dependencies:
            if dependency == name:
                return constraint
        return None


@dataclass(frozen=True)
class Package:
    name: str
    releases: tuple[Release, ...]

    def candidates(self, constraint: Range) -> tuple[Version, ...]:
        """Highest first: a resolver that starts low explores far more branches."""
        allowed = [item.version for item in self.releases if constraint.allows(item.version)]
        return tuple(sorted(allowed, reverse=True))


class Index:
    """A name -> releases map, validated once so the search never meets bad data."""

    def __init__(self, packages: dict[str, Package]) -> None:
        self._packages = packages

    def __contains__(self, name: str) -> bool:
        return name in self._packages

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._packages))

    def package(self, name: str) -> Package:
        try:
            return self._packages[name]
        except KeyError:
            raise IndexError_(f"{name!r} is not published in this index") from None

    def candidates(self, name: str, constraint: Range) -> tuple[Version, ...]:
        return self.package(name).candidates(constraint)

    def release(self, name: str, version: Version) -> Release:
        for item in self.package(name).releases:
            if item.version == version:
                return item
        raise IndexError_(f"{name} {version.text} is not published")

    def published(self, name: str) -> tuple[str, ...]:
        return tuple(item.version.text for item in self.package(name).releases)

    def as_dict(self) -> dict[str, list[str]]:
        return {name: list(self.published(name)) for name in self.names()}


def parse_index(payload: dict) -> Index:
    """Read {"packages": {"name": {"1.0.0": {"other": "^2.0"}}}}."""
    if not isinstance(payload, dict) or "packages" not in payload:
        raise IndexError_("an index needs a top-level 'packages' object")
    raw = payload["packages"]
    if not isinstance(raw, dict):
        raise IndexError_("'packages' must map a name to its versions")

    packages: dict[str, Package] = {}
    for name, versions in raw.items():
        if not isinstance(name, str) or not name:
            raise IndexError_(f"a package name must be a non-empty string, got {name!r}")
        if not isinstance(versions, dict) or not versions:
            raise IndexError_(
                f"{name} publishes no versions; a package nobody can install is not a package"
            )
        seen: dict[Version, None] = {}
        releases: list[Release] = []
        for text, dependencies in versions.items():
            try:
                version = parse(text)
            except VersionError as error:
                raise IndexError_(f"{name}: {error}") from error
            if version in seen:
                raise IndexError_(
                    f"{name} publishes {text!r} twice, once with build metadata: "
                    "two spellings of one version cannot both be installed"
                )
            seen[version] = None
            releases.append(Release(version, _parse_dependencies(name, version, dependencies)))
        packages[name] = Package(name, tuple(sorted(releases, key=lambda item: item.version)))

    index = Index(packages)
    _check_dependencies_exist(index)
    return index


def _parse_dependencies(name: str, version: Version, raw: object) -> tuple[tuple[str, Range], ...]:
    if raw is None:
        return ()
    if not isinstance(raw, dict):
        raise IndexError_(
            f"{name} {version.text}: dependencies must be an object of package -> range"
        )
    parsed: list[tuple[str, Range]] = []
    for dependency, constraint in raw.items():
        if not isinstance(constraint, str):
            raise IndexError_(f"{name} {version.text}: the range for {dependency} must be a string")
        try:
            parsed.append((dependency, parse_range(constraint)))
        except RangeError as error:
            raise IndexError_(f"{name} {version.text}: {error}") from error
    return tuple(sorted(parsed))


def _check_dependencies_exist(index: Index) -> None:
    """A missing package is an authoring error, not a resolution conflict.

    Finding it before the search means the search only ever reports conflicts
    that a reader can act on, and the message names the release that asks.
    """
    for name in index.names():
        for release in index.package(name).releases:
            for dependency, _ in release.dependencies:
                if dependency not in index:
                    raise IndexError_(
                        f"{name} {release.version.text} depends on {dependency!r}, "
                        "which this index does not publish"
                    )


def load(path: str | Path) -> Index:
    target = Path(path)
    try:
        payload = json.loads(target.read_text())
    except FileNotFoundError:
        raise IndexError_(f"no index at {target}") from None
    except json.JSONDecodeError as error:
        raise IndexError_(f"{target} is not JSON: {error}") from None
    try:
        return parse_index(payload)
    except IndexError_ as error:
        raise IndexError_(f"{target}: {error}") from None
