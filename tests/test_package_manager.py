"""--package-manager: one manager name that writes every command in a JS project."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from newstack import packagemanager
from newstack.cli import main
from newstack.registry import PACKAGE_MANAGER_NAMES, load_stacks

JS_STACKS = sorted(
    name for name, stack in load_stacks().items() if stack.chooses_package_manager
)


def _new(tmp_path: Path, stack: str, *extra: str, name: str = "pmproj") -> Path:
    dest = tmp_path / name
    code = main(["new", stack, str(dest), "--name", name, "--no-git", *extra])
    assert code == 0
    return dest


def _files(project: Path) -> str:
    """The two files a reader or CI acts on: the README and the workflow.

    .gitignore is deliberately not included: several templates ignore every
    manager's debug log at once, which is harmless and not a manager choice.
    """
    return "\n".join(
        [
            (project / "README.md").read_text(),
            (project / ".github/workflows/ci.yml").read_text(),
        ]
    )


def test_the_manager_table_matches_the_registry_vocabulary() -> None:
    assert set(packagemanager.CHOICES) == set(PACKAGE_MANAGER_NAMES)
    assert PACKAGE_MANAGER_NAMES[0] == packagemanager.DEFAULT


def test_every_javascript_stack_lists_npm_first() -> None:
    assert JS_STACKS, "no stack declares a package_manager — the registry changed shape"
    for name in JS_STACKS:
        stack = load_stacks()[name]
        assert stack.package_managers[0] == "npm", f"{name} does not default to npm"
        assert stack.language == "node", f"{name} declares a manager but is not a node stack"


def test_only_javascript_stacks_offer_the_choice() -> None:
    for name, stack in load_stacks().items():
        if stack.language != "node":
            assert not stack.chooses_package_manager, f"{name} should not offer --package-manager"


@pytest.mark.parametrize("stack_name", JS_STACKS)
def test_the_default_project_is_pure_npm(stack_name: str, tmp_path) -> None:
    project = _new(tmp_path, stack_name)
    text = _files(project)
    assert not re.search(r"(?<!\$)\{\{", text), "leftover placeholder"
    workflow = (project / ".github/workflows/ci.yml").read_text()
    assert "npm install --no-audit --no-fund" in workflow
    assert "pnpm" not in text and "yarn" not in text
    record = json.loads((project / ".newstack.json").read_text())
    assert record["context"]["package_manager"] == "npm"


@pytest.mark.parametrize("stack_name", JS_STACKS)
def test_every_javascript_workflow_installs_its_dependencies(
    stack_name: str, tmp_path
) -> None:
    """A workflow that runs tests before installing them tests nothing.

    ``node --test`` needs no packages, so a stack can look green on the runner
    while its npm dependencies were never installed -- and then the first
    dependency it gains fails CI instead of the code.
    """
    project = _new(tmp_path, stack_name)
    workflow = (project / ".github/workflows/ci.yml").read_text()
    assert packagemanager.BY_NAME["npm"].install in workflow


@pytest.mark.parametrize("manager", ["pnpm", "yarn"])
def test_choosing_a_manager_rewrites_every_command(manager: str, tmp_path) -> None:
    project = _new(tmp_path, "react-vite-ts", "--package-manager", manager)
    workflow = (project / ".github/workflows/ci.yml").read_text()
    chosen = packagemanager.BY_NAME[manager]
    assert f"- run: {chosen.install}" in workflow
    assert f"- run: {chosen.run} typecheck" in workflow
    assert f"- run: {chosen.test}" in workflow
    assert f"run: {chosen.setup}" in workflow
    assert "- name: Prepare " + manager in workflow
    readme = (project / "README.md").read_text()
    assert chosen.lock in readme
    assert chosen.ci_install in readme
    assert not re.search(r"(?<![a-z])npm ", readme), readme
    record = json.loads((project / ".newstack.json").read_text())
    assert record["context"]["package_manager"] == manager
    assert record["context"]["package_manager_lock"] == chosen.lock


def test_the_gitignore_follows_the_manager(tmp_path) -> None:
    npm_project = _new(tmp_path, "astro", name="a")
    pnpm_project = _new(tmp_path, "astro", "--package-manager", "pnpm", name="b")
    assert "npm-debug.log*" in (npm_project / ".gitignore").read_text()
    assert "pnpm-debug.log*" in (pnpm_project / ".gitignore").read_text()


def test_the_next_steps_name_the_chosen_manager(tmp_path, capsys) -> None:
    capsys.readouterr()
    _new(tmp_path, "node-express-ts", "--package-manager", "yarn")
    out = capsys.readouterr().out
    assert "yarn install" in out
    assert "yarn run dev" in out
    assert "npm install" not in out


def test_a_manager_the_stack_was_not_proven_with_is_refused(tmp_path, capsys) -> None:
    code = main(["new", "react-vite-ts", str(tmp_path / "x"), "--package-manager", "bun"])
    assert code == 1
    assert "supports npm, pnpm, yarn" in capsys.readouterr().err
    assert not (tmp_path / "x").exists()


def test_a_stack_without_the_choice_refuses_the_flag(tmp_path, capsys) -> None:
    code = main(["new", "python-cli", str(tmp_path / "x"), "--package-manager", "pnpm"])
    assert code == 1
    assert "no --package-manager choice" in capsys.readouterr().err
    assert not (tmp_path / "x").exists()


def test_update_keeps_the_recorded_manager(tmp_path) -> None:
    project = _new(tmp_path, "svelte-kit-ts", "--package-manager", "pnpm")
    assert main(["update", str(project)]) == 0
    workflow = (project / ".github/workflows/ci.yml").read_text()
    assert "pnpm install" in workflow
    record = json.loads((project / ".newstack.json").read_text())
    assert record["context"]["package_manager"] == "pnpm"


def test_update_switches_the_manager(tmp_path) -> None:
    project = _new(tmp_path, "vue-vite-ts", "--package-manager", "pnpm")
    assert main(["update", str(project), "--package-manager", "yarn"]) == 0
    workflow = (project / ".github/workflows/ci.yml").read_text()
    assert "yarn install" in workflow
    assert "pnpm" not in workflow
    readme = (project / "README.md").read_text()
    assert "yarn.lock" in readme
    record = json.loads((project / ".newstack.json").read_text())
    assert record["context"]["package_manager"] == "yarn"


def test_a_project_recorded_before_the_feature_still_updates(tmp_path) -> None:
    project = _new(tmp_path, "chrome-extension")
    record_path = project / ".newstack.json"
    record = json.loads(record_path.read_text())
    for key in packagemanager.KEYS:
        record["context"].pop(key, None)
    record_path.write_text(json.dumps(record))
    assert main(["update", str(project)]) == 0
    record = json.loads(record_path.read_text())
    assert record["context"]["package_manager"] == "npm"
    assert "npm install --no-audit --no-fund" in (project / ".github/workflows/ci.yml").read_text()


#: Stacks whose framework depends on vite itself, so the template need not.
VITE_FROM_FRAMEWORK = {"astro": "astro"}


@pytest.mark.parametrize("stack_name", JS_STACKS)
def test_a_vitest_stack_makes_vite_resolvable_without_peer_installs(stack_name: str) -> None:
    """npm and pnpm install vitest's `vite` peer dependency; yarn 1 does not."""
    data = json.loads((load_stacks()[stack_name].template_dir / "package.json").read_text())
    if "vitest" not in (data.get("scripts", {}).get("test") or ""):
        pytest.skip(f"{stack_name} does not run vitest")
    dev = data.get("devDependencies", {})
    framework = VITE_FROM_FRAMEWORK.get(stack_name)
    if framework:
        assert framework in {**data.get("dependencies", {}), **dev}, framework
        return
    assert "vite" in dev, (
        f"{stack_name} runs vitest without listing vite: npm and pnpm install that peer "
        "dependency automatically and yarn 1 does not, so `yarn test` dies with "
        "Cannot find package 'vite'"
    )


def test_each_manager_prepares_itself_in_ci() -> None:
    for manager in packagemanager.MANAGERS:
        assert manager.name in manager.setup, f"{manager.name} does not prepare itself"
        assert manager.name in manager.install or manager.name == "npm"

    assert packagemanager.BY_NAME["npm"].setup == "npm --version"
