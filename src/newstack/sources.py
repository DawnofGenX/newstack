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

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .registry import BUILTIN_ROOT, data_root, installed_root, load_stack

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
        checkout = Path(temporary) / "checkout"
        ok, output = _git(["clone", "--depth", "1", "--quiet", url, str(checkout)])
        if not ok:
            raise SourceError(f"could not clone {url}: {output}")
        ok, rev = _git(["rev-parse", "--short", "HEAD"], cwd=checkout)
        rev = rev if ok else ""

        candidates = _candidates(checkout, subdir)
        if not candidates:
            raise SourceError(
                f"{url}: no stack found — a stack is a directory with a stack.json "
                "and a template/ directory"
            )

        stage_root = Path(temporary) / "stage"
        validated = []
        for directory in candidates:
            staged = stage_root / (_declared_name(directory) or directory.name)
            shutil.copytree(directory, staged, ignore=shutil.ignore_patterns(".git"))
            try:
                validated.append(load_stack(staged))
            except Exception as exc:  # RegistryError, but never half-install
                raise SourceError(f"{url}: {exc}") from exc

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
        entries[stack.name] = {"url": stack.url, "rev": stack.rev, "added_at": stack.added_at}
    _write_installed(entries)
    return installed


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
