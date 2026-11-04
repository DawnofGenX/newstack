"""Stack discovery: every stack is a directory with a ``stack.json`` manifest."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

BUILTIN_ROOT = Path(__file__).resolve().parent / "data" / "stacks"
ENV_VAR = "NEWSTACK_STACKS"
ENV_HOME = "NEWSTACK_HOME"


class RegistryError(Exception):
    """A stack manifest is missing or malformed."""


@dataclass(frozen=True)
class VerifyStep:
    """One command that proves a generated project works."""

    name: str
    cmd: str
    tools: tuple[str, ...] = ()
    timeout: int = 600


@dataclass(frozen=True)
class DetectRule:
    """A marker that says "this directory looks like <stack>".

    ``contains`` makes the rule content-aware: the file must exist *and* contain the
    substring, which is how a Django project is told apart from any other pyproject.
    """

    file: str
    contains: str | None = None

    def _targets(self, directory: Path) -> list[Path]:
        """The files this rule looks at.

        A plain name is a single path. A name with a wildcard (``*.cabal``) is a
        glob, which is how a stack whose marker carries the project name can
        still be detected.
        """
        if any(character in self.file for character in "*?["):
            return sorted(path for path in directory.glob(self.file) if path.is_file())
        target = directory / self.file
        return [target] if target.is_file() else []

    def matches(self, directory: Path) -> bool:
        for target in self._targets(directory):
            if self.contains is None:
                return True
            try:
                if self.contains in target.read_text(encoding="utf-8", errors="ignore"):
                    return True
            except OSError:
                continue
        return False


@dataclass(frozen=True)
class Stack:
    name: str
    title: str
    language: str
    blurb: str
    requires: tuple[str, ...]
    verify: tuple[VerifyStep, ...]
    default_description: str
    next_steps: tuple[str, ...]
    directory: Path
    detect: tuple[DetectRule, ...] = ()
    detect_fallback: bool = False
    adopt: tuple[str, ...] = ()
    adopt_tests: tuple[str, ...] = ()

    @property
    def template_dir(self) -> Path:
        return self.directory / "template"

    @property
    def docs_url(self) -> str:
        return f"https://github.com/DawnofGenX/newstack/tree/main/src/newstack/data/stacks/{self.name}"

    def matches(self, directory: Path) -> bool:
        return any(rule.matches(directory) for rule in self.detect)

    @property
    def installed(self) -> bool:
        """True when this stack came from ``newstack stacks add``, not the package."""
        try:
            self.directory.resolve().relative_to(installed_root().resolve())
        except ValueError:
            return False
        return True


def _as_tuple(value: object, field: str, where: Path) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RegistryError(f"{where}: '{field}' must be a list of strings")
    return tuple(value)


def load_stack(directory: Path) -> Stack:
    manifest = directory / "stack.json"
    if not manifest.is_file():
        raise RegistryError(f"{directory}: missing stack.json")
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RegistryError(f"{manifest}: invalid JSON ({exc})") from exc
    if not isinstance(data, dict):
        raise RegistryError(f"{manifest}: top level must be an object")

    for key in ("name", "title", "language", "blurb"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise RegistryError(f"{manifest}: '{key}' must be a non-empty string")

    if data["name"] != directory.name:
        raise RegistryError(
            f"{manifest}: name '{data['name']}' must match directory '{directory.name}'"
        )

    raw_verify = data.get("verify", [])
    if not isinstance(raw_verify, list):
        raise RegistryError(f"{manifest}: 'verify' must be a list")
    steps: list[VerifyStep] = []
    for index, item in enumerate(raw_verify):
        if not isinstance(item, dict) or not isinstance(item.get("cmd"), str):
            raise RegistryError(f"{manifest}: verify[{index}] needs a 'cmd' string")
        steps.append(
            VerifyStep(
                name=str(item.get("name") or item["cmd"].split()[0]),
                cmd=item["cmd"],
                tools=_as_tuple(item.get("tools"), f"verify[{index}].tools", manifest),
                timeout=int(item.get("timeout", 600)),
            )
        )

    if not (directory / "template").is_dir():
        raise RegistryError(f"{directory}: missing template/ directory")

    rules: list[DetectRule] = []
    raw_detect = data.get("detect", [])
    if not isinstance(raw_detect, list):
        raise RegistryError(f"{manifest}: 'detect' must be a list")
    for index, item in enumerate(raw_detect):
        if not isinstance(item, dict) or not isinstance(item.get("file"), str):
            raise RegistryError(f"{manifest}: detect[{index}] needs a 'file' string")
        contains = item.get("contains")
        if contains is not None and not isinstance(contains, str):
            raise RegistryError(f"{manifest}: detect[{index}].contains must be a string")
        rules.append(DetectRule(file=item["file"], contains=contains))

    fallback = data.get("detect_fallback", False)
    if not isinstance(fallback, bool):
        raise RegistryError(f"{manifest}: 'detect_fallback' must be a boolean")

    return Stack(
        name=data["name"],
        title=data["title"],
        language=data["language"],
        blurb=data["blurb"],
        requires=_as_tuple(data.get("requires"), "requires", manifest),
        verify=tuple(steps),
        default_description=str(data.get("default_description") or f"A {data['title']} project."),
        next_steps=_as_tuple(data.get("next_steps"), "next_steps", manifest),
        directory=directory,
        detect=tuple(rules),
        detect_fallback=fallback,
        adopt=_as_tuple(data.get("adopt"), "adopt", manifest),
        adopt_tests=_as_tuple(data.get("adopt_tests"), "adopt_tests", manifest),
    )


def data_root() -> Path:
    """Where installed stacks and their manifest live.

    ``NEWSTACK_HOME`` wins so tests and throwaway sandboxes can stay hermetic;
    otherwise this follows the XDG data directory.
    """
    override = os.environ.get(ENV_HOME, "").strip()
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME", "").strip()
    base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share"
    return base / "newstack"


def installed_root() -> Path:
    """Where ``newstack stacks add`` puts stacks."""
    return data_root() / "stacks"


def search_roots() -> list[Path]:
    """Discovery order: built-in stacks, then installed ones, then ``NEWSTACK_STACKS``.

    Built-in first means a shipped stack can never be shadowed by accident: an
    installed stack with the same name is ignored, and ``stacks add`` refuses to
    create one in the first place.
    """
    roots = [BUILTIN_ROOT, installed_root()]
    extra = os.environ.get(ENV_VAR, "")
    for entry in extra.split(os.pathsep):
        if entry.strip():
            roots.append(Path(entry).expanduser())
    return roots


@dataclass(frozen=True)
class Catalog:
    """Every stack that loaded, plus the ones that did not.

    A stack directory is under construction for as long as a subagent is writing it:
    ``stack.json`` lands first, ``template/`` last. Loading must therefore be able to
    report a broken stack without taking the whole catalog down with it — otherwise a
    half-written stack makes ``list`` and ``check --all`` unusable for every other stack.
    """

    stacks: dict[str, Stack]
    errors: dict[str, str]


def load_stacks() -> dict[str, Stack]:
    return load_catalog(allow_partial=False).stacks


def load_catalog(allow_partial: bool = True) -> Catalog:
    stacks: dict[str, Stack] = {}
    errors: dict[str, str] = {}
    for root in search_roots():
        if not root.is_dir():
            continue
        for directory in sorted(p for p in root.iterdir() if p.is_dir()):
            if not (directory / "stack.json").is_file():
                continue
            try:
                stack = load_stack(directory)
            except RegistryError as exc:
                if not allow_partial:
                    raise
                errors[directory.name] = str(exc)
                continue
            stacks[stack.name] = stack
    return Catalog(dict(sorted(stacks.items())), dict(sorted(errors.items())))



def get_stack(name: str) -> Stack:
    stacks = load_stacks()
    try:
        return stacks[name]
    except KeyError:
        available = ", ".join(stacks) or "(none found)"
        raise RegistryError(f"unknown stack '{name}' — available: {available}") from None
