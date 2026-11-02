"""Template rendering and file generation.

Deliberately dependency-free: templates are plain files with ``{{ variable }}``
placeholders, rendered by a regex substitution. No Jinja, no JS runtime, so
``uvx newstack`` starts in well under a second and works offline.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

VAR_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s*\}\}")


class TemplateError(Exception):
    """A template could not be rendered or written."""


_MISSING = object()


def _lookup(context: dict, dotted: str) -> object:
    value: object = context
    for part in dotted.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return _MISSING
    return value


def render_string(text: str, context: dict, *, missing: list[str] | None = None) -> str:
    """Replace every ``{{ key }}`` in *text* using *context* (dotted keys allowed).

    Two escapes keep templating out of the way of the languages we generate:

    * ``${{ ... }}`` is left untouched, so GitHub Actions expressions pass through.
    * ``{{!`` emits a literal ``{{``.
    """

    def _sub(match: re.Match[str]) -> str:
        if match.start() and text[match.start() - 1] == "$":
            return match.group(0)
        value = _lookup(context, match.group(1))
        if value is _MISSING:
            if missing is not None:
                missing.append(match.group(1))
            return match.group(0)
        return "" if value is None else str(value)

    return VAR_RE.sub(_sub, text).replace("{{!", "{{")


@dataclass
class GenerateResult:
    root: Path
    files: list[str] = field(default_factory=list)
    directories: list[str] = field(default_factory=list)
    overwritten: list[str] = field(default_factory=list)
    dry_run: bool = False

    @property
    def count(self) -> int:
        return len(self.files)


def _safe_relpath(rel: str, source: str) -> str:
    candidate = Path(rel)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise TemplateError(f"refusing to write outside the project: {rel!r} (from {source})")
    return candidate.as_posix()


@dataclass(frozen=True)
class _Entry:
    rel: str
    payload: bytes
    executable: bool


def _collect(template_dir: Path, context: dict) -> tuple[list[_Entry], list[str]]:
    """Render the whole template in memory first, so a bad template writes nothing."""
    missing: list[str] = []
    entries: list[_Entry] = []
    directories: list[str] = []

    for src in sorted(template_dir.rglob("*")):
        if src.is_dir() and src.name == "__pycache__":
            continue
        rel_src = src.relative_to(template_dir).as_posix()
        rel = _safe_relpath(render_string(rel_src, context, missing=missing), rel_src)
        if src.is_dir():
            directories.append(rel)
            continue

        raw = src.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            payload = raw
        else:
            payload = render_string(text, context, missing=missing).encode("utf-8")

        executable = bool(os.access(src, os.X_OK) or src.suffix in {".sh", ".command"})
        entries.append(_Entry(rel=rel, payload=payload, executable=executable))

    if missing:
        names = ", ".join(sorted(set(missing)))
        raise TemplateError(f"unknown template variable(s) in {template_dir.name}: {names}")
    return entries, directories


def render_tree(
    template_dir: Path | str, context: dict
) -> tuple[list[tuple[str, bytes, bool]], list[str]]:
    """Render a template in memory: ``[(relpath, payload, executable)], [dirs]``.

    Used by ``adopt``, which needs to inspect rendered content before deciding whether
    to write anything. Raises :class:`TemplateError` on unknown variables.
    """
    entries, directories = _collect(Path(template_dir), context)
    return [(entry.rel, entry.payload, entry.executable) for entry in entries], directories


def generate(
    template_dir: Path | str,
    destination: Path | str,
    context: dict,
    *,
    force: bool = False,
    dry_run: bool = False,
) -> GenerateResult:
    """Render *template_dir* into *destination*.

    Raises :class:`TemplateError` on unknown variables, path escapes, or a
    non-empty destination without ``force``. Nothing is written until the whole
    template has rendered successfully.
    """
    template_dir = Path(template_dir)
    destination = Path(destination)
    if not template_dir.is_dir():
        raise TemplateError(f"template directory not found: {template_dir}")

    if destination.exists() and not destination.is_dir():
        raise TemplateError(f"destination exists and is not a directory: {destination}")
    if destination.is_dir() and any(destination.iterdir()) and not force:
        raise TemplateError(
            f"destination is not empty: {destination} (use --force to write into it anyway)"
        )

    entries, directories = _collect(template_dir, context)
    result = GenerateResult(root=destination, dry_run=dry_run)
    result.directories = directories
    result.files = [entry.rel for entry in entries]

    if dry_run:
        return result

    destination.mkdir(parents=True, exist_ok=True)
    for rel_dir in directories:
        (destination / rel_dir).mkdir(parents=True, exist_ok=True)

    for entry in entries:
        target = destination / entry.rel
        if target.exists():
            result.overwritten.append(entry.rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(entry.payload)
        if entry.executable:
            target.chmod(0o755)

    return result
