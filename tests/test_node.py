"""--node: one floor that writes every version-bearing line of a JS project."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from newstack.cli import main
from newstack.registry import load_stacks

NODE_STACKS = sorted(name for name, stack in load_stacks().items() if stack.language == "node")


def _new(tmp_path: Path, stack: str, *extra: str, name: str = "prov") -> Path:
    dest = tmp_path / name
    code = main(["new", stack, str(dest), "--name", name, "--no-git", *extra])
    assert code == 0
    return dest


def _matrix(project: Path) -> list[str]:
    """Every Node major the generated workflow actually runs."""
    workflow = (project / ".github/workflows/ci.yml").read_text()
    line = next(line for line in workflow.splitlines() if "node-version: [" in line) if (
        "node-version: [" in workflow
    ) else next(
        line for line in workflow.splitlines() if "node-version: \"" in line
    )
    return re.findall(r'"(\d+)"', line)


def _engines(project: Path) -> str:
    data = json.loads((project / "package.json").read_text())
    return data.get("engines", {}).get("node", "")


def test_every_node_stack_declares_the_majors_it_is_proven_on() -> None:
    assert NODE_STACKS, "no node stacks found — the registry changed shape"
    for name in NODE_STACKS:
        stack = load_stacks()[name]
        assert stack.is_node, f"{name} is a node stack but has no 'node' key"
        assert stack.node_minimum in stack.node_versions


@pytest.mark.parametrize("stack_name", NODE_STACKS)
def test_the_default_floor_matches_the_template(stack_name: str, tmp_path) -> None:
    project = _new(tmp_path, stack_name)
    stack = load_stacks()[stack_name]
    workflow = (project / ".github/workflows/ci.yml").read_text()
    engines = _engines(project)
    # astro and vue-vite told npm about a floor before --node existed; every other
    # stack gained the field with this feature, so all of them must name it now.
    assert engines == f">={stack.node_minimum}", f"{stack_name}: {engines!r}"
    # GitHub's own `${{ … }}` interpolation is not a leftover placeholder
    assert not re.search(r"(?<!\$)\{\{", workflow)
    if "node-version: [" in workflow:
        assert _matrix(project) == list(stack.node_versions)
    else:  # a single-version workflow runs the floor and nothing else
        assert _matrix(project) == [stack.node_minimum]


def test_raising_the_floor_rewrites_the_matrix_engines_and_readme(tmp_path) -> None:
    project = _new(tmp_path, "react-vite-ts", "--node", "24")
    workflow = (project / ".github/workflows/ci.yml").read_text()
    assert 'node-version: ["24"]' in workflow
    assert '"22"' not in workflow
    assert _engines(project) == ">=24"
    record = json.loads((project / ".newstack.json").read_text())
    assert record["context"]["node_version"] == "24"


def test_the_readme_follows_the_floor(tmp_path) -> None:
    project = _new(tmp_path, "vue-vite-ts", "--node", "24")
    readme = (project / "README.md").read_text()
    assert "Node.js 24 or newer" in readme
    assert "Node.js 22.18" not in readme
    assert "on Node.js 24 for every push" in readme


def test_a_major_the_stack_was_not_proven_on_is_refused(tmp_path, capsys) -> None:
    code = main(["new", "react-vite-ts", str(tmp_path / "x"), "--node", "20"])
    assert code == 1
    assert "supports Node 22, 24" in capsys.readouterr().err
    assert not (tmp_path / "x").exists()


def test_astro_cannot_be_asked_for_a_node_it_refuses(tmp_path, capsys) -> None:
    code = main(["new", "astro", str(tmp_path / "x"), "--node", "22"])
    assert code == 1
    assert "supports Node 24" in capsys.readouterr().err


def test_a_stack_without_a_node_choice_refuses_the_flag(tmp_path, capsys) -> None:
    code = main(["new", "go-cli", str(tmp_path / "x"), "--node", "22"])
    assert code == 1
    assert "no --node choice" in capsys.readouterr().err


def test_update_keeps_the_recorded_floor(tmp_path) -> None:
    project = _new(tmp_path, "node-express-ts", "--node", "24")
    assert main(["update", str(project)]) == 0
    assert _engines(project) == ">=24"
    record = json.loads((project / ".newstack.json").read_text())
    assert record["context"]["node_version"] == "24"


def test_update_moves_the_floor(tmp_path) -> None:
    project = _new(tmp_path, "node-express-ts", "--node", "22")
    assert main(["update", str(project), "--node", "24"]) == 0
    assert _engines(project) == ">=24"
    workflow = (project / ".github/workflows/ci.yml").read_text()
    assert 'node-version: ["24"]' in workflow
    record = json.loads((project / ".newstack.json").read_text())
    assert record["context"]["node_version"] == "24"


def test_a_project_recorded_before_the_feature_still_updates(tmp_path) -> None:
    project = _new(tmp_path, "chrome-extension")
    record_path = project / ".newstack.json"
    record = json.loads(record_path.read_text())
    record["context"].pop("node_version", None)
    record_path.write_text(json.dumps(record))
    assert main(["update", str(project)]) == 0
    assert _engines(project) == ">=22"
