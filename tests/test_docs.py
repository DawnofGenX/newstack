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


def test_readme_lists_each_stack_exactly_once() -> None:
    """A duplicated row is drift too: it makes the table count lie about the registry."""
    rows = _readme_rows()
    duplicated = sorted({name for name in rows if rows.count(name) > 1})
    assert not duplicated, f"README stack table lists twice: {', '.join(duplicated)}"
    assert sorted(rows) == sorted(load_stacks()), (
        f"README has {len(rows)} rows for {len(load_stacks())} stacks"
    )


def _ci_matrix_blocks() -> dict[str, list[str]]:
    """Map each stack-sharding job in ci.yml to the names in its matrix, in file order.

    The stack job is split across several matrices (see docs/CI.md): a single
    matrix stops expanding once it reaches 256 entries, and a matrix that does
    not expand makes the run fail with no per-stack jobs at all.
    """
    lines = CI.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line == "jobs:")
    except StopIteration:  # pragma: no cover - a workflow without jobs is not a workflow
        raise AssertionError("ci.yml has no top-level `jobs:` section") from None
    blocks: dict[str, list[str]] = {}
    job: str | None = None
    in_matrix = False
    for line in lines[start + 1 :]:
        header = re.match(r"^ {2}([A-Za-z0-9_-]+):\s*$", line)
        if header:
            job, in_matrix = header.group(1), False
            continue
        if line.strip() == "stack:" and job is not None:
            in_matrix = True
            blocks.setdefault(job, [])
            continue
        if in_matrix and job is not None:
            if line.startswith("          - "):
                blocks[job].append(line.strip()[2:].strip())
            elif line.strip():
                in_matrix = False
    return blocks


def _ci_matrix_entries() -> list[str]:
    """Every stack named by any shard matrix, in file order."""
    return [name for entries in _ci_matrix_blocks().values() for name in entries]


def test_ci_matrix_lists_each_stack_exactly_once() -> None:
    """A duplicate matrix entry runs the same stack twice and hides a missing one."""
    entries = _ci_matrix_entries()
    duplicated = sorted({name for name in entries if entries.count(name) > 1})
    assert not duplicated, f"ci.yml stack matrices list twice: {', '.join(duplicated)}"
    assert sorted(entries) == sorted(load_stacks()), (
        f"ci.yml matrices name {len(entries)} stacks for {len(load_stacks())} in the registry"
    )


def test_every_shard_matrix_stays_under_the_github_limit() -> None:
    """Past 256 entries GitHub silently drops the matrix, so the run proves nothing.

    That is not a slowdown: the job does not expand at all, no `stack X` job is
    created, and the run just reports a failure. Keep every shard well under.
    """
    blocks = _ci_matrix_blocks()
    assert blocks, "ci.yml has no `stack:` matrix to check"
    too_big = {job: len(entries) for job, entries in blocks.items() if len(entries) > 256}
    assert not too_big, f"matrix over the 256-job expansion cap (it will not expand): {too_big}"


def test_shard_matrices_are_balanced() -> None:
    """One empty or one giant shard means the split stopped doing its job."""
    sizes = [len(entries) for entries in _ci_matrix_blocks().values() if entries]
    assert sizes, "ci.yml has no non-empty stack matrix"
    assert min(sizes) > 0
    assert max(sizes) <= 2 * min(sizes), f"shard sizes are lopsided: {sorted(sizes)}"


def test_stack_shards_share_one_step_list() -> None:
    """Four copies of the 60-odd toolchain gates drift apart on the first edit."""
    text = CI.read_text(encoding="utf-8")
    blocks = _ci_matrix_blocks()
    assert len(blocks) > 1, "expected the stack job to be sharded"
    assert text.count("x-shared-steps: &shared_setup") == 1, (
        "ci.yml must define the shared step list exactly once, as `x-shared-steps: &shared_setup`"
    )
    used = text.count("    steps: *shared_setup")
    assert used == len(blocks), f"{len(blocks)} stack jobs share the steps, {used} do"
    anchor = text.split("x-shared-steps: &shared_setup", 1)[1].split("\njobs:", 1)[0]
    assert "fromJSON(" in anchor, "the toolchain gates must live in the shared step list"
    assert anchor.count("      - name:") + anchor.count("  - name:") >= 20, (
        "the shared step list looks truncated"
    )


def test_readme_states_no_stack_count_that_can_go_stale() -> None:
    """A hardcoded count is drift bait once a stack is added; the table is the source."""
    text = README.read_text(encoding="utf-8")
    assert not re.search(r"\b(\d+|six|seven|eight|nine|ten)\s+(stacks|starters)\b", text, re.I)
