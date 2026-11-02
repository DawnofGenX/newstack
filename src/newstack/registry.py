"""Stack discovery: every stack is a directory with a ``stack.json`` manifest."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

BUILTIN_ROOT = Path(__file__).resolve().parent / "data" / "stacks"
ENV_VAR = "NEWSTACK_STACKS"


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

    def matches(self, directory: Path) -> bool:
        target = directory / self.file
        if not target.is_file():
            return False
        if self.contains is None:
            return True
        try:
            return self.contains in target.read_text(encoding="utf-8", errors="ignore")
        except OSError:
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


def search_roots() -> list[Path]:
    """Built-in stacks first; ``NEWSTACK_STACKS`` entries may override them by name."""
    roots = [BUILTIN_ROOT]
    extra = os.environ.get(ENV_VAR, "")
    for entry in extra.split(os.pathsep):
        if entry.strip():
            roots.append(Path(entry).expanduser())
    return roots


def load_stacks() -> dict[str, Stack]:
    stacks: dict[str, Stack] = {}
    for root in search_roots():
        if not root.is_dir():
            continue
        for directory in sorted(p for p in root.iterdir() if p.is_dir()):
            if (directory / "stack.json").is_file():
                stack = load_stack(directory)
                stacks[stack.name] = stack
    return dict(sorted(stacks.items()))


def get_stack(name: str) -> Stack:
    stacks = load_stacks()
    try:
        return stacks[name]
    except KeyError:
        available = ", ".join(stacks) or "(none found)"
        raise RegistryError(f"unknown stack '{name}' — available: {available}") from None
