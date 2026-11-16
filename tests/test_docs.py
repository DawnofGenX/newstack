"""Docs drift guards: the README and CI must not fall behind the registry."""

from __future__ import annotations

import re
from pathlib import Path

from newstack.registry import load_stacks

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
CI = ROOT / ".github" / "workflows" / "ci.yml"


def test_readme_exists() -> None:
    assert README.is_file()


def test_every_stack_is_in_the_readme_table() -> None:
    text = README.read_text(encoding="utf-8")
    missing = [name for name in load_stacks() if f"| `{name}` |" not in text]
    assert not missing, f"README stack table is missing: {', '.join(missing)}"


def test_every_stack_is_in_the_ci_matrix() -> None:
    text = CI.read_text(encoding="utf-8")
    missing = []
    for name in load_stacks():
        pattern = rf"^\s*-\s*{re.escape(name)}\s*$"
        if not re.search(pattern, text, re.M):
            missing.append(name)
    assert not missing, f"ci.yml stack matrix is missing: {', '.join(missing)}"


def _readme_rows() -> list[str]:
    """Stack names in the README table, one per row, in file order."""
    text = README.read_text(encoding="utf-8")
    return re.findall(r"^\|\s*`([a-z0-9][a-z0-9-]*)`\s*\|", text, re.M)


def _ci_matrix_entries() -> list[str]:
    """Names under the `stack:` matrix key, in file order."""
    lines = CI.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.strip() == "stack:")
    entries: list[str] = []
    for line in lines[start + 1 :]:
        if not line.strip():
            continue
        if not line.startswith("          - "):
            break
        entries.append(line.strip()[2:].strip())
    return entries


def test_readme_lists_each_stack_exactly_once() -> None:
    """A duplicated row is drift too: it makes the table count lie about the registry."""
    rows = _readme_rows()
    duplicated = sorted({name for name in rows if rows.count(name) > 1})
    assert not duplicated, f"README stack table lists twice: {', '.join(duplicated)}"
    assert sorted(rows) == sorted(load_stacks()), (
        f"README has {len(rows)} rows for {len(load_stacks())} stacks"
    )


def test_ci_matrix_lists_each_stack_exactly_once() -> None:
    """A duplicate matrix entry runs the same stack twice and hides a missing one."""
    entries = _ci_matrix_entries()
    duplicated = sorted({name for name in entries if entries.count(name) > 1})
    assert not duplicated, f"ci.yml stack matrix lists twice: {', '.join(duplicated)}"
    assert sorted(entries) == sorted(load_stacks()), (
        f"ci.yml matrix has {len(entries)} entries for {len(load_stacks())} stacks"
    )


def test_readme_states_no_stack_count_that_can_go_stale() -> None:
    """A hardcoded count is drift bait once a stack is added; the table is the source."""
    text = README.read_text(encoding="utf-8")
    assert not re.search(r"\b(\d+|six|seven|eight|nine|ten)\s+(stacks|starters)\b", text, re.I)
