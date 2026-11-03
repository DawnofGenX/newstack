"""End-to-end checks on the shipped stacks.

The structural tests always run. The expensive ones (installing and building each
generated project) run when NEWSTACK_RUN_VERIFY=1, which is what CI sets.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

import pytest

from newstack.registry import load_stacks, search_roots
from newstack.verify import check_stack, missing_tools

USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)\s*$", re.MULTILINE)
ACTION_REF_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[^@]+)?@v\d+(?:\.\d+)*$")

STACK_NAMES = sorted(load_stacks())


def test_stacks_were_discovered() -> None:
    assert len(STACK_NAMES) >= 6


@pytest.mark.parametrize("name", STACK_NAMES)
def test_workflow_actions_are_pinned_to_major_versions(tmp_path, name: str) -> None:
    from newstack.cli import build_context_for_check
    from newstack.registry import get_stack
    from newstack.render import generate

    stack = get_stack(name)
    context = build_context_for_check(stack, "sample-app")
    generate(stack.template_dir, tmp_path, context)

    workflows = list(tmp_path.glob(".github/workflows/*.yml")) + list(
        tmp_path.glob(".github/workflows/*.yaml")
    )
    assert workflows, f"{name} ships no CI workflow"
    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        assert "jobs:" in text, workflow
        assert "runs-on:" in text, workflow
        for ref in USES_RE.findall(text):
            assert ACTION_REF_RE.match(ref), f"{workflow.name}: unpinned or odd action ref {ref!r}"


@pytest.mark.parametrize("name", STACK_NAMES)
def test_action_refs_are_resolvable_style(tmp_path, name: str) -> None:
    """Moving major tags are fine for actions/*, but setup-uv publishes exact tags only."""
    from newstack.cli import build_context_for_check
    from newstack.registry import get_stack
    from newstack.render import generate

    stack = get_stack(name)
    context = build_context_for_check(stack, "sample-app")
    generate(stack.template_dir, tmp_path, context)

    for workflow in tmp_path.glob(".github/workflows/*.y*ml"):
        for ref in USES_RE.findall(workflow.read_text(encoding="utf-8")):
            if ref.startswith("astral-sh/setup-uv@"):
                tag = ref.split("@", 1)[1]
                assert re.fullmatch(r"v\d+\.\d+\.\d+", tag), (
                    f"{workflow.name}: setup-uv has no moving major tag, pin the patch "
                    f"version (got {tag!r})"
                )


@pytest.mark.parametrize("name", STACK_NAMES)
def test_uv_pip_installs_target_the_generated_venv(name: str) -> None:
    """`uv run` exports VIRTUAL_ENV, so a bare `uv pip install` would fill the wrong venv."""
    from newstack.registry import get_stack

    stack = get_stack(name)
    for step in stack.verify:
        if "uv pip install" in step.cmd:
            assert "--python .venv/bin/python" in step.cmd, (
                f"{name}: '{step.name}' must pin --python .venv/bin/python "
                "(otherwise uv installs into an inherited VIRTUAL_ENV)"
            )


@pytest.mark.parametrize("name", STACK_NAMES)
def test_npm_ci_requires_a_committed_lockfile(tmp_path, name: str) -> None:
    """`npm ci` fails without package-lock.json, which a fresh scaffold does not have."""
    from newstack.cli import build_context_for_check
    from newstack.registry import get_stack
    from newstack.render import generate

    stack = get_stack(name)
    context = build_context_for_check(stack, "sample-app")
    generate(stack.template_dir, tmp_path, context)

    for workflow in tmp_path.glob(".github/workflows/*.y*ml"):
        lines = [
            line for line in workflow.read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")
        ]
        if any("npm ci" in line for line in lines):
            assert (tmp_path / "package-lock.json").is_file(), (
                f"{name}/{workflow.name} runs `npm ci` but the template ships no "
                "package-lock.json, so the generated project's first CI run would fail"
            )


@pytest.mark.parametrize("name", STACK_NAMES)
def test_stack_manifest_is_consistent(name: str) -> None:
    from newstack.registry import get_stack

    stack = get_stack(name)
    manifest = json.loads((stack.directory / "stack.json").read_text(encoding="utf-8"))
    assert manifest["name"] == name
    assert manifest["blurb"].strip()
    assert stack.next_steps, f"{name} has no next_steps"
    assert any("test" in step.name for step in stack.verify), f"{name} never runs a test"
    assert any(root in (stack.directory, *search_roots()) for root in search_roots())


@pytest.mark.skipif(
    os.environ.get("NEWSTACK_RUN_VERIFY") != "1",
    reason="set NEWSTACK_RUN_VERIFY=1 to install and build every generated stack",
)
@pytest.mark.parametrize("name", STACK_NAMES)
def test_generated_stack_actually_works(name: str) -> None:
    from newstack.cli import build_context_for_check
    from newstack.registry import get_stack

    stack = get_stack(name)
    absent = missing_tools(stack)
    if absent:
        pytest.skip(f"missing toolchain: {', '.join(absent)}")

    context = build_context_for_check(stack, "check-app")
    result = check_stack(stack, context, verbose=False)
    details = "\n".join(
        f"{o.name}: ok={o.ok} skipped={o.skipped}\n{o.output}" for o in result.outcomes
    )
    assert result.ok, f"{name} failed verification:\n{details}"


def test_no_stack_leaks_a_local_checkout_path() -> None:
    for stack in load_stacks().values():
        for root, _dirs, files in os.walk(stack.template_dir):
            for filename in files:
                path = Path(root) / filename
                text = path.read_text(encoding="utf-8", errors="ignore")
                assert "/home/hermes" not in text, path
                assert str(shutil.os.getcwd()) not in text, path


@pytest.mark.parametrize("name", STACK_NAMES)
def test_shipped_ci_matrix_satisfies_requires_python(name: str) -> None:
    """A shipped workflow must not test a Python the package refuses to install on.

    Copying one stack's workflow into another is the easy way to inherit a matrix that
    includes versions below the new stack's requires-python floor.
    """
    from newstack.registry import get_stack

    stack = get_stack(name)
    pyproject = stack.template_dir / "pyproject.toml"
    workflow = stack.template_dir / ".github" / "workflows" / "ci.yml"
    if not pyproject.is_file() or not workflow.is_file():
        pytest.skip("not a Python stack")

    spec = re.search(r'requires-python\s*=\s*"([^"]+)"', pyproject.read_text(encoding="utf-8"))
    matrix = re.search(r"python-version:\s*\[([^\]]+)\]", workflow.read_text(encoding="utf-8"))
    if not spec or not matrix:
        pytest.skip("no requires-python or no matrix")

    floor_match = re.search(r">=\s*(\d+)\.(\d+)", spec.group(1))
    assert floor_match, f"{name}: cannot parse requires-python {spec.group(1)!r}"
    floor = (int(floor_match.group(1)), int(floor_match.group(2)))
    versions = [
        tuple(int(part) for part in item.strip().strip('"').strip("'").split("."))
        for item in matrix.group(1).split(",")
    ]
    too_old = [f"{v[0]}.{v[1]}" for v in versions if v < floor]
    assert not too_old, (
        f"{name}: shipped CI tests Python {', '.join(too_old)} but requires-python is "
        f"{spec.group(1)} — those jobs cannot install the package"
    )
