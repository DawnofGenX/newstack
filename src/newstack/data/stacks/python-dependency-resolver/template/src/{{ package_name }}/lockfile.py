"""A lockfile is a promise that the same tree comes back tomorrow."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .index import Index
from .resolver import Resolution, ResolveError, resolve
from .versions import Version, VersionError, parse

FORMAT = 1


class LockError(ValueError):
    """Raised when a lockfile cannot be trusted."""


@dataclass(frozen=True)
class Lock:
    packages: dict[str, Version]
    path: Path | None = None

    def versions(self) -> dict[str, Version]:
        return dict(self.packages)


@dataclass
class Drift:
    """One reason the lockfile and the index disagree."""

    package: str
    reason: str

    def line(self) -> str:
        return f"  {self.package:<18} {self.reason}"


def parse_lock(payload: object) -> Lock:
    if not isinstance(payload, dict):
        raise LockError("a lockfile must be an object")
    version = payload.get("version")
    if version != FORMAT:
        raise LockError(
            f"lockfile format {version!r} is not {FORMAT}; refusing to guess at a format "
            "that may mean something else"
        )
    packages = payload.get("packages")
    if not isinstance(packages, dict) or not packages:
        raise LockError("a lockfile with no packages locks nothing")

    parsed: dict[str, Version] = {}
    for name, text in packages.items():
        if not isinstance(text, str):
            raise LockError(f"{name}: the locked version must be a string")
        try:
            parsed[name] = parse(text)
        except VersionError as error:
            raise LockError(f"{name}: {error}") from error
    return Lock(parsed)


def read(path: str | Path) -> Lock:
    target = Path(path)
    try:
        payload = json.loads(target.read_text())
    except FileNotFoundError:
        raise LockError(f"no lockfile at {target}") from None
    except json.JSONDecodeError as error:
        raise LockError(f"{target} is not JSON: {error}") from None
    try:
        return Lock(parse_lock(payload).packages, target)
    except LockError as error:
        raise LockError(f"{target}: {error}") from None


def render(resolution: Resolution) -> str:
    """Sorted keys and a trailing newline: a lockfile that churns on nothing."""
    body = {
        "version": FORMAT,
        "packages": {name: resolution.version(name).text for name in sorted(resolution.choices)},
    }
    return json.dumps(body, indent=2, sort_keys=False) + "\n"


def write(path: str | Path, resolution: Resolution) -> Path:
    target = Path(path)
    target.write_text(render(resolution))
    return target


def changed(before: Lock, after: Resolution) -> list[str]:
    """Only real changes, in a stable order, so a diff of the lock is readable."""
    lines: list[str] = []
    for name in sorted(set(before.packages) | set(after.choices)):
        old = before.packages.get(name)
        new = after.version(name) if name in after.choices else None
        if old is None and new is not None:
            lines.append(f"  + {name} {new.text}")
        elif old is not None and new is None:
            lines.append(f"  - {name} {old.text}")
        elif old is not None and new is not None and old != new:
            lines.append(f"  ~ {name} {old.text} -> {new.text}")
    return lines


def audit(index: Index, lock: Lock, roots: dict[str, str]) -> list[Drift]:
    """Resolve from the lock and name every place the promise is out of date.

    A newer version existing is NOT drift: an update is a decision, and a check
    that fails whenever the registry moves would fail on somebody else's release.
    """
    drift: list[Drift] = []
    try:
        resolution = resolve(index, roots, locked=lock.packages)
    except ResolveError as error:
        return [Drift("(roots)", f"the requirements do not resolve: {error}")]

    for name in sorted(set(lock.packages) - set(resolution.choices)):
        drift.append(Drift(name, f"locked at {lock.packages[name].text} but nothing needs it"))
    for name in sorted(resolution.choices):
        chosen = resolution.version(name)
        locked = lock.packages.get(name)
        if locked is None:
            drift.append(Drift(name, f"missing from the lock; the index resolves {chosen.text}"))
        elif locked != chosen:
            drift.append(
                Drift(name, f"locked at {locked.text}, but the requirements select {chosen.text}")
            )

    for entry in drift:
        if entry.package == "(roots)":
            return drift
    return drift
