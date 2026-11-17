#!/usr/bin/env python
"""Wire a newly added stack into README.md and the shortest CI shard matrix."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from difflib import unified_diff
from pathlib import Path


class WireError(Exception):
    """A user-facing wiring error."""


README_ROW_RE = re.compile(r"^\|\s*`([a-z0-9][a-z0-9-]*)`\s*\|", re.M)


def _opt(args, *names):
    for name in names:
        value = getattr(args, name, None)
        if value is not None:
            return value
    return None


def _env(*names):
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def resolve_paths(args):
    root = _opt(args, "root", "repo_root", "repo")
    if root is None:
        root = _env("NEWSTACK_ROOT", "WIRE_STACK_ROOT", "REPO_ROOT")
    root = Path(root).expanduser() if root else Path.cwd()

    readme = _opt(args, "readme", "readme_path")
    if readme is None:
        readme = _env("README_PATH", "WIRE_README", "README")
    readme = Path(readme).expanduser() if readme else root / "README.md"

    ci = _opt(args, "ci", "ci_path", "ci_yml", "workflow", "workflow_path")
    if ci is None:
        ci = _env("CI_PATH", "WIRE_CI", "CI_YML", "WORKFLOW_PATH")
    ci = Path(ci).expanduser() if ci else root / ".github" / "workflows" / "ci.yml"

    stacks = _opt(args, "stacks_dir", "stacks_root", "stacks", "data_dir", "data_root")
    if stacks is None:
        stacks = _env("STACKS_DIR", "STACKS_ROOT", "DATA_DIR", "NEWSTACK_STACKS_DIR")
    stacks = Path(stacks).expanduser() if stacks else root / "src" / "newstack" / "data" / "stacks"

    return root, readme, ci, stacks


def load_stack_manifest(stacks_root: Path, name: str):
    manifest_path = stacks_root / name / "stack.json"
    if not manifest_path.is_file():
        raise WireError(f"stack manifest not found: {manifest_path}")
    try:
        raw = manifest_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise WireError(f"cannot read stack manifest {manifest_path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise WireError(f"invalid JSON in {manifest_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise WireError(f"{manifest_path}: top level must be a JSON object")
    return data, manifest_path


def is_wired(name: str, readme_text: str, ci_text: str) -> bool:
    if re.search(rf"^\|\s*`{re.escape(name)}`\s*\|", readme_text, re.M):
        return True
    return bool(re.search(rf"^          -\s*{re.escape(name)}\s*$", ci_text, re.M))


def _parse_ci(text: str):
    lines = text.splitlines(keepends=True)
    start = None
    for i, line in enumerate(lines):
        if line.rstrip("\r\n") == "jobs:":
            start = i
            break
    if start is None:
        raise WireError("ci.yml has no top-level `jobs:` section")

    blocks: dict[str, list[tuple[int, str]]] = {}
    stack_key_index: dict[str, int] = {}
    job_order: list[str] = []
    job: str | None = None
    in_matrix = False

    for idx in range(start + 1, len(lines)):
        line = lines[idx]
        header = re.match(r"^ {2}([A-Za-z0-9_-]+):\s*$", line.rstrip("\r\n"))
        if header:
            job = header.group(1)
            in_matrix = False
            continue
        if line.rstrip("\r\n").strip() == "stack:" and job is not None:
            in_matrix = True
            if job not in blocks:
                blocks[job] = []
                job_order.append(job)
            stack_key_index[job] = idx
            continue
        if in_matrix and job is not None:
            if line.startswith("          - "):
                entry = line.strip()[2:].strip()
                blocks[job].append((idx, entry))
            elif line.strip():
                in_matrix = False
    return blocks, stack_key_index, job_order, lines


def validate_ci(text: str) -> None:
    blocks, _keys, _order, _lines = _parse_ci(text)
    if not blocks:
        raise WireError("ci.yml has no `stack:` matrix to check")
    sizes = {job: len(entries) for job, entries in blocks.items()}
    too_big = {job: n for job, n in sizes.items() if n > 256}
    if too_big:
        raise WireError(
            "refusing to write: a shard matrix would exceed GitHub's 256-entry "
            f"expansion cap: {too_big}"
        )
    if any(n <= 0 for n in sizes.values()):
        raise WireError("refusing to write: a shard matrix is empty")
    if max(sizes.values()) > 2 * min(sizes.values()):
        raise WireError(
            "refusing to write: shard matrices would be unbalanced "
            f"(sizes={sorted(sizes.values())}, rule max <= 2*min)"
        )


def _readme_row_text(name: str, data: dict) -> str:
    desc = (
        data.get("blurb")
        or data.get("description")
        or data.get("default_description")
        or data.get("title")
        or name
    )
    desc = " ".join(str(desc).split())
    desc = desc.replace("|", "\\|")
    language = str(data.get("language", "")).strip()
    language = language.replace("|", "\\|")
    return f"| `{name}` | {desc} | {language} |\n"


def plan_changes(name: str, data: dict, readme_text: str, ci_text: str):
    readme_lines = readme_text.splitlines(keepends=True)
    row_indices = [i for i, line in enumerate(readme_lines) if README_ROW_RE.match(line)]
    row_names = [README_ROW_RE.match(readme_lines[i]).group(1) for i in row_indices]

    insert_at = None
    for idx, row_name in zip(row_indices, row_names, strict=False):
        if row_name > name:
            insert_at = idx
            break
    if insert_at is None:
        insert_at = row_indices[-1] + 1 if row_indices else len(readme_lines)

    new_row = _readme_row_text(name, data)
    new_readme_lines = list(readme_lines)
    new_readme_lines.insert(insert_at, new_row)
    new_readme_text = "".join(new_readme_lines)

    blocks, stack_key_index, job_order, ci_lines = _parse_ci(ci_text)
    if not job_order:
        raise WireError("ci.yml has no shard matrix (`stacks-a` .. `stacks-d`)")

    best_size = min(len(blocks[j]) for j in job_order)
    chosen = None
    for job in job_order:
        if len(blocks[job]) == best_size:
            chosen = job
            break
    assert chosen is not None

    entries = blocks[chosen]
    insert_ci_at = entries[-1][0] + 1 if entries else stack_key_index[chosen] + 1

    new_ci_lines = list(ci_lines)
    new_ci_lines.insert(insert_ci_at, f"          - {name}\n")
    new_ci_text = "".join(new_ci_lines)

    return new_readme_text, new_ci_text, chosen


def plan_removal(name: str, readme_text: str, ci_text: str):
    """Drop every README row and matrix entry for `name`.

    A stack that turns out to duplicate an existing one has to be unwired
    before it is deleted, otherwise README and the shard matrices keep
    pointing at a directory that no longer exists.
    """
    row_re = re.compile(rf"^\|\s*`{re.escape(name)}`\s*\|")
    readme_lines = readme_text.splitlines(keepends=True)
    kept_readme = [line for line in readme_lines if not row_re.match(line)]
    readme_removed = len(readme_lines) - len(kept_readme)

    ci_lines = ci_text.splitlines(keepends=True)
    entry_line = f"          - {name}"
    kept_ci = [line for line in ci_lines if line.rstrip("\r\n") != entry_line]
    ci_removed = len(ci_lines) - len(kept_ci)

    return "".join(kept_readme), "".join(kept_ci), readme_removed, ci_removed


def print_diff(
    readme_text: str,
    new_readme_text: str,
    readme_path: Path,
    ci_text: str,
    new_ci_text: str,
    ci_path: Path,
) -> None:
    parts = []
    for old, new, path in (
        (readme_text, new_readme_text, readme_path),
        (ci_text, new_ci_text, ci_path),
    ):
        diff = "".join(
            unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=str(path),
                tofile=str(path),
            )
        )
        if diff:
            parts.append(diff)
    sys.stdout.write("".join(parts))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Wire a stack into README.md and ci.yml")
    parser.add_argument("name", help="stack name to wire")
    parser.add_argument("--dry-run", action="store_true", help="print changes without writing")
    parser.add_argument(
        "--remove",
        action="store_true",
        help="unwire a stack: drop its README row and every CI shard entry",
    )
    parser.add_argument("--root", "--repo-root", "--repo", dest="root", default=None)
    parser.add_argument("--readme", "--readme-path", dest="readme", default=None)
    parser.add_argument(
        "--ci", "--ci-yml", "--ci-path", "--workflow", "--workflow-path",
        dest="ci", default=None,
    )
    parser.add_argument(
        "--stacks-dir", "--stacks-root", "--stacks", "--data-dir", "--data-root",
        dest="stacks_dir", default=None,
    )
    args = parser.parse_args(argv)

    try:
        _root, readme_path, ci_path, stacks_root = resolve_paths(args)
        readme_text = readme_path.read_text(encoding="utf-8")
        ci_text = ci_path.read_text(encoding="utf-8")

        if args.remove:
            new_readme_text, new_ci_text, row_count, entry_count = plan_removal(
                args.name, readme_text, ci_text
            )
            if not row_count and not entry_count:
                print(f"{args.name} is not wired; no changes.")
                return 0
            validate_ci(new_ci_text)
            if args.dry_run:
                print_diff(readme_text, new_readme_text, readme_path, ci_text, new_ci_text, ci_path)
                return 0
            readme_path.write_text(new_readme_text, encoding="utf-8")
            ci_path.write_text(new_ci_text, encoding="utf-8")
            print(
                f"Unwired {args.name}: -{row_count} README row, "
                f"-{entry_count} CI entry."
            )
            return 0

        data, _manifest = load_stack_manifest(stacks_root, args.name)

        if is_wired(args.name, readme_text, ci_text):
            print(f"{args.name} is already wired; no changes.")
            return 0

        new_readme_text, new_ci_text, chosen = plan_changes(
            args.name, data, readme_text, ci_text
        )

        validate_ci(new_ci_text)

        if args.dry_run:
            print_diff(readme_text, new_readme_text, readme_path, ci_text, new_ci_text, ci_path)
            return 0

        readme_path.write_text(new_readme_text, encoding="utf-8")
        ci_path.write_text(new_ci_text, encoding="utf-8")
        print(f"Wired {args.name}: +1 README row, +1 entry in {chosen}.")
        return 0
    except WireError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
