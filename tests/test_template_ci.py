"""Template CI guards: a scaffolded project's workflow must only run that project's own code.

Nothing in newstack's own matrix ever executes a template ``ci.yml`` - it only runs inside a
project created by ``newstack new`` - so copy-paste drift between stacks stays invisible until
the user's first CI run. These guards cover the two shapes that actually bit us:

* a workflow that builds a binary belonging to another stack (``go build -o bin/jsonlq .``
  shipped in eight stacks that have no ``jsonlq`` command);
* a workflow whose steps call subcommands of another stack's CLI (the sign/verify steps of
  the HMAC webhook verifier copied into three unrelated Ruby CLIs, which fails outright).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from newstack.registry import search_roots

BINARY = re.compile(r"\bbin/([A-Za-z0-9][A-Za-z0-9_.-]*)")


def _template_workflows() -> list[tuple[Path, Path]]:
    """Every stack directory that ships a template CI workflow, as (stack dir, workflow)."""
    found: list[tuple[Path, Path]] = []
    for root in search_roots():
        if not Path(root).is_dir():  # the installed/extra roots only exist once a user adds one
            continue
        for stack_dir in sorted(Path(root).iterdir()):
            workflow = stack_dir / "template" / ".github" / "workflows" / "ci.yml"
            if workflow.is_file():
                found.append((stack_dir, workflow))
    return found


def _tree_text(template_dir: Path, skip: Path) -> str:
    chunks: list[str] = []
    for path in sorted(template_dir.rglob("*")):
        if not path.is_file() or path == skip:
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:  # binaries in the tree are not evidence of a name
            continue
    return "\n".join(chunks)


def test_a_template_workflow_only_runs_its_own_binaries() -> None:
    offenders: list[str] = []
    for stack_dir, workflow in _template_workflows():
        text = workflow.read_text(encoding="utf-8")
        template_dir = stack_dir / "template"
        # A name is the stack's own when the rest of its project - or the manifest's own build
        # and verify commands - mentions it. A name that appears nowhere else came from a
        # copy-paste and produces a binary nobody asked for.
        haystack = _tree_text(template_dir, workflow)
        haystack += (stack_dir / "stack.json").read_text(encoding="utf-8")
        for literal in BINARY.findall(text):
            if literal not in haystack:
                offenders.append(f"{stack_dir.name}: bin/{literal}")
    assert not offenders, (
        "these template workflows reference a binary that the stack never mentions: "
        + ", ".join(sorted(set(offenders)))
    )


def test_ruby_rake_cli_stacks_share_one_workflow() -> None:
    workflows: dict[str, str] = {}
    for stack_dir, workflow in _template_workflows():
        manifest = json.loads((stack_dir / "stack.json").read_text(encoding="utf-8"))
        if manifest.get("language") != "ruby":
            continue
        if "bundle" in manifest.get("requires", []):  # rails-app and ruby-sinatra bundle
            continue
        if not (stack_dir / "template" / "Rakefile").is_file():
            continue
        workflows[stack_dir.name] = workflow.read_text(encoding="utf-8")

    assert workflows, "no rake based ruby stacks were found"
    reference_name = sorted(workflows)[0]
    reference = workflows[reference_name]
    drifted = sorted(name for name, text in workflows.items() if text != reference)
    assert not drifted, (
        f"{', '.join(drifted)} drifted from {reference_name}'s workflow; the shared Ruby CLI "
        "workflow must stay identical so scaffolding any of them produces the same CI"
    )
    assert "rake test" in reference and "bash smoke.sh" in reference
