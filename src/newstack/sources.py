"""Stacks that come from outside the package: ``newstack stacks add <git-url>``.

A shipped stack is proven by this repository's CI. An installed one is not — the
command says so, and ``newstack check <name>`` is how you get the same proof
locally. Keeping that distinction visible is the point: it is the difference
between "newstack generated this and it builds" and "someone published this".

Layout under the data root::

    <data root>/stacks/<name>/…     the stack directory, as it appeared in the repo
    <data root>/sources.json        where each one came from, and when
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .registry import BUILTIN_ROOT, Stack, data_root, installed_root, load_stack

MANIFEST = "sources.json"


class SourceError(Exception):
    """A repository could not be installed as a stack."""


@dataclass(frozen=True)
class Installed:
    name: str
    path: Path
    url: str
    rev: str
    added_at: str

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "path": str(self.path),
            "url": self.url,
            "rev": self.rev,
            "added_at": self.added_at,
        }


@dataclass(frozen=True)
class Refreshed:
    """What ``stacks update`` did to one installed stack."""

    name: str
    url: str
    old_rev: str
    new_rev: str
    changed: bool

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "old_rev": self.old_rev,
            "new_rev": self.new_rev,
            "changed": self.changed,
        }


@dataclass(frozen=True)
class Remote:
    """Whether an installed stack's repository has moved since it was pulled."""

    name: str
    url: str
    installed_rev: str
    remote_rev: str
    behind: bool
    error: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "installed_rev": self.installed_rev,
            "remote_rev": self.remote_rev,
            "behind": self.behind,
            "error": self.error,
        }


def manifest_path() -> Path:
    return data_root() / MANIFEST


def read_installed() -> dict[str, dict]:
    """The recorded origin of every installed stack (missing or broken → empty)."""
    try:
        data = json.loads(manifest_path().read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {name: entry for name, entry in data.items() if isinstance(entry, dict)}


def _write_installed(entries: dict[str, dict]) -> None:
    path = manifest_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dict(sorted(entries.items())), indent=2) + "\n"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(payload, encoding="utf-8")
    os.replace(temporary, path)


def _git(args: list[str], cwd: Path | str | None = None) -> tuple[bool, str]:
    try:
        completed = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True, check=False
        )
    except OSError as exc:  # git is not installed at all
        return False, str(exc)
    if completed.returncode != 0:
        return False, (completed.stderr or completed.stdout).strip()
    return True, completed.stdout.strip()


def _candidates(checkout: Path, subdir: str | None) -> list[Path]:
    """The directories in a checkout that look like stacks."""
    if subdir:
        base = checkout / subdir
        if not base.is_dir():
            raise SourceError(f"{checkout.name}: no '{subdir}' directory in the repository")
        roots = [base]
    else:
        roots = [checkout]
        roots.extend(sorted(p for p in checkout.iterdir() if p.is_dir() and p.name != ".git"))

    found: list[Path] = []
    for root in roots:
        if (root / "stack.json").is_file():
            found.append(root)
            continue
        # one level deeper, so a repo with stacks/<name>/ also works
        found.extend(sorted(p for p in root.iterdir() if (p / "stack.json").is_file()))
    unique: list[Path] = []
    for path in found:
        if path not in unique:
            unique.append(path)
    return unique


def _declared_name(directory: Path) -> str:
    """The ``name`` a candidate claims, before the manifest is validated.

    A stack in the root of a repository is cloned into a directory named after the
    repository, not after the stack, so the candidates are staged under their
    declared name and validated there — the same name they will be installed as.
    """
    try:
        data = json.loads((directory / "stack.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    name = data.get("name") if isinstance(data, dict) else None
    return name if isinstance(name, str) else ""


def builtin_names() -> set[str]:
    return {
        directory.name
        for directory in BUILTIN_ROOT.iterdir()
        if (directory / "stack.json").is_file()
    } if BUILTIN_ROOT.is_dir() else set()


def _stage(
    url: str,
    subdir: str | None,
    temporary: Path,
    expected: tuple[str, ...] = (),
) -> tuple[str, list[Stack]]:
    """Clone *url* and validate every stack it carries, inside *temporary*."""
    checkout = temporary / "checkout"
    ok, output = _git(["clone", "--depth", "1", "--quiet", url, str(checkout)])
    if not ok:
        raise SourceError(f"could not clone {url}: {output}")
    ok, rev = _git(["rev-parse", "--short", "HEAD"], cwd=checkout)
    rev = rev if ok else ""

    candidates = _candidates(checkout, subdir)
    if not candidates:
        if expected:
            raise SourceError(
                f"{url}: no longer contains {', '.join(sorted(expected))} — "
                "the installed copy was left alone"
            )
        raise SourceError(
            f"{url}: no stack found — a stack is a directory with a stack.json "
            "and a template/ directory"
        )

    stage_root = temporary / "stage"
    validated: list[Stack] = []
    for directory in candidates:
        staged = stage_root / (_declared_name(directory) or directory.name)
        shutil.copytree(directory, staged, ignore=shutil.ignore_patterns(".git"))
        try:
            validated.append(load_stack(staged))
        except Exception as exc:  # RegistryError, but never half-install
            raise SourceError(f"{url}: {exc}") from exc
    return rev, validated


def _tree_digest(directory: Path) -> str:
    """A digest of a stack directory's file names and contents."""
    digest = hashlib.sha256()
    for path in sorted(p for p in directory.rglob("*") if p.is_file()):
        digest.update(path.relative_to(directory).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def install(
    url: str,
    *,
    subdir: str | None = None,
    force: bool = False,
) -> list[Installed]:
    """Clone *url*, validate the stacks it carries, and install them.

    Nothing is written until every stack in the repository has been validated and
    every name has been checked against the shipped and installed ones, so a
    repository with one broken stack installs none of them.
    """
    if not shutil.which("git"):
        raise SourceError("git is required to install a stack from a repository")
    if not url.strip():
        raise SourceError("a repository URL is required")

    target_root = installed_root()
    shipped = builtin_names()
    with tempfile.TemporaryDirectory(prefix="newstack-add-") as temporary:
        rev, validated = _stage(url, subdir, Path(temporary))
        clashes = [stack.name for stack in validated if stack.name in shipped]
        if clashes:
            raise SourceError(
                f"{url}: {', '.join(sorted(clashes))} already ships with newstack — "
                "rename the stack directory in that repository"
            )
        existing = {path.name for path in target_root.iterdir()} if target_root.is_dir() else set()
        present = [stack.name for stack in validated if stack.name in existing and not force]
        if present:
            raise SourceError(
                f"already installed: {', '.join(sorted(present))} (use --force to replace)"
            )

        added_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        installed: list[Installed] = []
        target_root.mkdir(parents=True, exist_ok=True)
        for stack in validated:
            target = target_root / stack.name
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(stack.directory, target, ignore=shutil.ignore_patterns(".git"))
            installed.append(
                Installed(
                    name=stack.name,
                    path=target,
                    url=url,
                    rev=rev,
                    added_at=added_at,
                )
            )

    entries = read_installed()
    for stack in installed:
        entries[stack.name] = {
            "url": stack.url,
            "rev": stack.rev,
            "added_at": stack.added_at,
            "subdir": subdir,
        }
    _write_installed(entries)
    return installed


def update(name: str | None = None) -> list[Refreshed]:
    """Re-pull installed stacks from the repositories they came from.

    *name* refreshes one stack; omitting it refreshes every installed stack that
    has a recorded origin. Everything is cloned and validated before anything is
    replaced, so a repository that went bad — or that dropped a stack — leaves
    the installed copy exactly as it was.
    """
    present = {entry.name: entry for entry in list_installed()}
    if name is not None:
        if name not in present:
            raise SourceError(f"'{name}' is not installed (see `newstack stacks list`)")
        if not present[name].url:
            raise SourceError(f"'{name}' has no recorded origin — reinstall it with `stacks add`")
        targets = [present[name]]
    else:
        targets = [entry for entry in present.values() if entry.url]
        if not targets:
            raise SourceError(
                "no installed stack has a recorded origin — nothing to refresh"
                if present
                else "no stacks installed (see `newstack stacks add <git-url>`)"
            )

    if not shutil.which("git"):
        raise SourceError("git is required to update a stack from a repository")

    entries_meta = read_installed()
    by_url: dict[str, list[Installed]] = {}
    for entry in targets:
        by_url.setdefault(entry.url, []).append(entry)

    results: list[Refreshed] = []
    for url, entries in by_url.items():
        subdir = entries_meta.get(entries[0].name, {}).get("subdir")
        subdir = subdir if isinstance(subdir, str) and subdir else None
        with tempfile.TemporaryDirectory(prefix="newstack-update-") as temporary:
            rev, validated = _stage(
                url, subdir, Path(temporary), tuple(entry.name for entry in entries)
            )
            by_name = {stack.name: stack for stack in validated}
            missing = [entry.name for entry in entries if entry.name not in by_name]
            if missing:
                raise SourceError(
                    f"{url}: no longer contains {', '.join(sorted(missing))} — "
                    "the installed copy was left alone"
                )
            added_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            for entry in entries:
                stack = by_name[entry.name]
                changed = _tree_digest(stack.directory) != _tree_digest(entry.path)
                if changed:
                    shutil.rmtree(entry.path)
                    shutil.copytree(
                        stack.directory, entry.path, ignore=shutil.ignore_patterns(".git")
                    )
                    entries_meta[entry.name] = {
                        **entries_meta.get(entry.name, {}),
                        "url": url,
                        "rev": rev,
                        "updated_at": added_at,
                    }
                results.append(
                    Refreshed(
                        name=entry.name,
                        url=url,
                        old_rev=entry.rev,
                        new_rev=rev,
                        changed=changed,
                    )
                )

    _write_installed(entries_meta)
    return results


def outdated(name: str | None = None) -> list[Remote]:
    """Which installed stacks have moved upstream, without cloning anything.

    ``git ls-remote`` resolves the repository's default branch to a commit id, which
    is the whole question — an installed stack is current when its recorded revision
    is that commit. A repository that cannot be reached is reported, not raised: one
    unreachable origin should not hide the state of the others.
    """
    present = list_installed()
    if name is not None:
        present = [entry for entry in present if entry.name == name]
        if not present:
            raise SourceError(f"'{name}' is not installed (see `newstack stacks list`)")
    if not present:
        installed_any = bool(list_installed())
        raise SourceError(
            "no installed stack has a recorded origin — nothing to compare"
            if installed_any
            else "no stacks installed (see `newstack stacks add <git-url>`)"
        )

    results: list[Remote] = []
    for entry in present:
        if not entry.url:
            results.append(Remote(entry.name, "", entry.rev, "", False, "no recorded origin"))
            continue
        ok, output = _git(["ls-remote", entry.url, "HEAD"])
        if not ok:
            results.append(
                Remote(entry.name, entry.url, entry.rev, "", False, output or "unreachable")
            )
            continue
        remote_rev = output.split()[0][:7] if output.split() else ""
        behind = bool(remote_rev) and not remote_rev.startswith(entry.rev) if entry.rev else True
        results.append(Remote(entry.name, entry.url, entry.rev, remote_rev, behind))
    return results


def remove(name: str) -> Path:
    """Delete an installed stack. Shipped stacks cannot be removed."""
    target = installed_root() / name
    if name in builtin_names():
        raise SourceError(f"'{name}' ships with newstack and cannot be removed")
    if not target.is_dir():
        raise SourceError(f"'{name}' is not installed (see `newstack stacks list`)")
    shutil.rmtree(target)
    entries = read_installed()
    entries.pop(name, None)
    _write_installed(entries)
    return target


def list_installed() -> list[Installed]:
    """Installed stacks that still exist on disk, with whatever origin we recorded."""
    root = installed_root()
    if not root.is_dir():
        return []
    entries = read_installed()
    found: list[Installed] = []
    for directory in sorted(p for p in root.iterdir() if (p / "stack.json").is_file()):
        meta = entries.get(directory.name, {})
        found.append(
            Installed(
                name=directory.name,
                path=directory,
                url=str(meta.get("url", "")),
                rev=str(meta.get("rev", "")),
                added_at=str(meta.get("added_at", "")),
            )
        )
    return found
