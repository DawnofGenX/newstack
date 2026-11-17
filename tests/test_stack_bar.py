"""Executable quality bar for every stack.

See docs/STACK-BAR.md. The bar is deliberately mechanical: a stack either ships
the required proof files or it is listed in docs/bar-exceptions.json with a
one-line reason, and the allowlist itself is checked for sanity.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from newstack.registry import load_stacks

ROOT = Path(__file__).resolve().parent.parent
STACKS_DIR = ROOT / "src" / "newstack" / "data" / "stacks"
EXCEPTIONS_FILE = ROOT / "docs" / "bar-exceptions.json"


def _exceptions() -> dict[str, str]:
    data = json.loads(EXCEPTIONS_FILE.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "bar-exceptions.json must be an object"
    for key, value in data.items():
        assert isinstance(key, str) and key.strip(), "exception key must be a stack name"
        assert isinstance(value, str) and value.strip(), (
            f"exception for {key!r} needs a one-line reason"
        )
    return data


def _has_selftest(stack_dir: Path) -> bool:
    return any(stack_dir.rglob("selftest.py"))


def test_bar_exceptions_file_is_sane() -> None:
    """The allowlist must not name missing stacks or stacks that already ship proof."""
    stacks = load_stacks()
    exceptions = _exceptions()

    unknown = sorted(name for name in exceptions if name not in stacks)
    assert not unknown, f"bar-exceptions names non-existent stacks: {', '.join(unknown)}"

    non_python = sorted(
        name for name in exceptions if not stacks[name].is_python
    )
    assert not non_python, f"bar-exceptions lists non-Python stacks: {', '.join(non_python)}"

    has_selftest = sorted(
        name for name in exceptions if _has_selftest(stacks[name].template_dir)
    )
    assert not has_selftest, (
        f"bar-exceptions lists stacks that already ship selftest.py: {', '.join(has_selftest)}"
    )


def test_every_stack_ships_smoke_sh() -> None:
    """Each stack must ship an executable template/smoke.sh."""
    stacks = load_stacks()
    missing = []
    not_executable = []
    for name, stack in stacks.items():
        smoke = stack.template_dir / "smoke.sh"
        if not smoke.is_file():
            missing.append(name)
        elif not os.access(smoke, os.X_OK):
            not_executable.append(name)
    failures = []
    if missing:
        failures.append(f"missing smoke.sh ({len(missing)}): {', '.join(sorted(missing))}")
    if not_executable:
        failures.append(
            f"smoke.sh not executable ({len(not_executable)}): "
            f"{', '.join(sorted(not_executable))}"
        )
    assert not failures, "\n".join(failures)


def test_every_python_stack_has_selftest_or_exception() -> None:
    """Python stacks need selftest.py unless allowlisted in bar-exceptions.json."""
    stacks = load_stacks()
    exceptions = set(_exceptions())
    missing = [
        name
        for name, stack in stacks.items()
        if stack.is_python
        and name not in exceptions
        and not _has_selftest(stack.template_dir)
    ]
    assert not missing, (
        f"python stacks without selftest.py ({len(missing)}): {', '.join(sorted(missing))}"
    )


def test_every_stack_ships_readme() -> None:
    """Each stack must ship a template/README.md."""
    stacks = load_stacks()
    missing = [
        name
        for name, stack in stacks.items()
        if not (stack.template_dir / "README.md").is_file()
    ]
    assert not missing, f"stacks without README.md ({len(missing)}): {', '.join(sorted(missing))}"
