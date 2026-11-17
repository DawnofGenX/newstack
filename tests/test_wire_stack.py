"""Tests for scripts/wire_stack.py, operating only on temporary copies."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "wire_stack.py"
README_SRC = ROOT / "README.md"
CI_SRC = ROOT / ".github" / "workflows" / "ci.yml"


def _copy_repo(tmp_path: Path) -> Path:
    (tmp_path / "README.md").write_text(README_SRC.read_text(encoding="utf-8"), encoding="utf-8")
    ci_dir = tmp_path / ".github" / "workflows"
    ci_dir.mkdir(parents=True, exist_ok=True)
    (ci_dir / "ci.yml").write_text(CI_SRC.read_text(encoding="utf-8"), encoding="utf-8")
    return tmp_path


def _make_stack(root: Path, name: str) -> None:
    stack_dir = root / "src" / "newstack" / "data" / "stacks" / name
    stack_dir.mkdir(parents=True, exist_ok=True)
    (stack_dir / "stack.json").write_text(
        json.dumps({"name": name, "title": name, "language": "python", "blurb": "a test stack"}),
        encoding="utf-8",
    )


def _count_readme_rows(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    return len(re.findall(r"^\|\s*`[a-z0-9][a-z0-9-]*`\s*\|", text, re.M))


def _ci_blocks(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line == "jobs:")
    blocks: dict[str, list[str]] = {}
    job = None
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


def _run(root: Path, name: str, *extra: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), name, "--root", str(root), *extra],
        capture_output=True,
        text=True,
    )


def test_wires_new_name(tmp_path):
    root = _copy_repo(tmp_path)
    _make_stack(root, "zz-test-stack")
    readme_before = _count_readme_rows(root / "README.md")
    ci_before = _ci_blocks(root / ".github" / "workflows" / "ci.yml")
    total_before = sum(len(v) for v in ci_before.values())
    shortest_before = min(len(v) for v in ci_before.values())

    res = _run(root, "zz-test-stack")
    assert res.returncode == 0, res.stderr

    assert _count_readme_rows(root / "README.md") == readme_before + 1
    ci_after = _ci_blocks(root / ".github" / "workflows" / "ci.yml")
    assert sum(len(v) for v in ci_after.values()) == total_before + 1
    # the shard that grew was one of the shortest before
    grown = [j for j in ci_before if len(ci_after[j]) == len(ci_before[j]) + 1]
    assert len(grown) == 1
    assert len(ci_before[grown[0]]) == shortest_before


def test_second_run_changes_nothing(tmp_path):
    root = _copy_repo(tmp_path)
    _make_stack(root, "zz-test-stack")
    _run(root, "zz-test-stack")
    readme_bytes = (root / "README.md").read_bytes()
    ci_bytes = (root / ".github" / "workflows" / "ci.yml").read_bytes()

    res = _run(root, "zz-test-stack")
    assert res.returncode == 0
    assert (root / "README.md").read_bytes() == readme_bytes
    assert (root / ".github" / "workflows" / "ci.yml").read_bytes() == ci_bytes


def test_missing_stack_errors(tmp_path):
    root = _copy_repo(tmp_path)
    res = _run(root, "zz-does-not-exist")
    assert res.returncode != 0


def test_invalid_json_errors(tmp_path):
    root = _copy_repo(tmp_path)
    stack_dir = root / "src" / "newstack" / "data" / "stacks" / "zz-bad-json"
    stack_dir.mkdir(parents=True, exist_ok=True)
    (stack_dir / "stack.json").write_text("{not json", encoding="utf-8")
    res = _run(root, "zz-bad-json")
    assert res.returncode != 0


def test_dry_run_does_not_write(tmp_path):
    root = _copy_repo(tmp_path)
    _make_stack(root, "zz-test-stack")
    readme_bytes = (root / "README.md").read_bytes()
    ci_bytes = (root / ".github" / "workflows" / "ci.yml").read_bytes()

    res = _run(root, "zz-test-stack", "--dry-run")
    assert res.returncode == 0
    assert (root / "README.md").read_bytes() == readme_bytes
    assert (root / ".github" / "workflows" / "ci.yml").read_bytes() == ci_bytes
    assert "+ " in res.stdout or "zz-test-stack" in res.stdout


def test_full_shard_refused(tmp_path):
    root = _copy_repo(tmp_path)
    _make_stack(root, "zz-test-stack")
    ci_path = root / ".github" / "workflows" / "ci.yml"
    text = ci_path.read_text(encoding="utf-8")
    # bloat stacks-a to 256 entries by adding dummy entries
    lines = text.splitlines(keepends=True)
    # find last entry line in stacks-a matrix: insert dummies before its steps line
    # Simple approach: replace first occurrence of "    steps: &shared_setup" marker
    marker = "    steps: &shared_setup\n"
    idx = lines.index(marker)
    dummies = "".join(f"          - dummy-{i}\n" for i in range(256))
    # Insert 256 dummies before the shared step list to overflow the cap.
    lines.insert(idx, dummies)
    ci_path.write_text("".join(lines), encoding="utf-8")

    readme_bytes = (root / "README.md").read_bytes()
    ci_bytes = ci_path.read_bytes()

    res = _run(root, "zz-test-stack")
    assert res.returncode != 0, res.stdout
    assert (root / "README.md").read_bytes() == readme_bytes
    assert ci_path.read_bytes() == ci_bytes


def test_balance_rule_enforced(tmp_path):
    root = _copy_repo(tmp_path)
    _make_stack(root, "zz-test-stack")
    ci_path = root / ".github" / "workflows" / "ci.yml"
    text = ci_path.read_text(encoding="utf-8")
    # Make stacks-d huge relative to stacks-a by duplicating its entries 5x? Instead
    # shrink: remove most entries from stacks-a? Simpler: append a huge block to stacks-d
    # to create imbalance such that adding to shortest (stacks-a) keeps max>2*min.
    # We'll empty stacks-b/c/d? Instead make stacks-a have 1 entry and others 100.
    # Easiest: rewrite not trivial. Use approach: bloat stacks-d with 200 dummy entries.
    lines = text.splitlines(keepends=True)
    # find stacks-d matrix: locate "  stacks-d:" then its steps marker at end
    start = next(i for i, ln in enumerate(lines) if ln.strip() == "stacks-d:")
    # find next "    steps: *shared_setup" after start
    end = next(i for i in range(start, len(lines)) if lines[i].strip() == "steps: *shared_setup")
    dummies = "".join(f"          - dummy-{i}\n" for i in range(200))
    lines.insert(end, dummies)
    ci_path.write_text("".join(lines), encoding="utf-8")

    readme_bytes = (root / "README.md").read_bytes()
    ci_bytes = ci_path.read_bytes()

    res = _run(root, "zz-test-stack")
    # Adding to shortest (stacks-a, ~79 entries) yields ~80; stacks-d ~278; max>2*min -> refuse
    assert res.returncode != 0, res.stdout
    assert (root / "README.md").read_bytes() == readme_bytes
    assert ci_path.read_bytes() == ci_bytes
