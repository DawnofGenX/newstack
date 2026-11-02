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


def test_readme_states_no_stack_count_that_can_go_stale() -> None:
    """A hardcoded count is drift bait once a stack is added; the table is the source."""
    text = README.read_text(encoding="utf-8")
    assert not re.search(r"\b(\d+|six|seven|eight|nine|ten)\s+(stacks|starters)\b", text, re.I)
