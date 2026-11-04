"""--python: one floor that writes every version-bearing line of the project."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from newstack.cli import main
from newstack.registry import load_stacks

PYTHON_STACKS = sorted(
    name for name, stack in load_stacks().items() if stack.language == "python"
)


def _new(tmp_path: Path, stack: str, *extra: str, name: str = "prov") -> Path:
    dest = tmp_path / name
    code = main(["new", stack, str(dest), "--name", name, "--no-git", *extra])
    assert code == 0
    return dest


def _matrix(project: Path) -> list[str]:
    workflow = (project / ".github/workflows/ci.yml").read_text()
    line = next(
        line for line in workflow.splitlines() if "python-version: [" in line
    )
    return re.findall(r'"(\d+\.\d+)"', line)


def test_every_python_stack_declares_the_versions_it_is_proven_on() -> None:
    assert PYTHON_STACKS, "no python stacks found — the registry changed shape"
    for name in PYTHON_STACKS:
        stack = load_stacks()[name]
        assert stack.is_python, f"{name} is a python stack but has no 'python' key"
        assert stack.python_minimum in stack.python_versions


@pytest.mark.parametrize("stack_name", PYTHON_STACKS)
def test_the_default_floor_matches_the_template(stack_name: str, tmp_path) -> None:
    project = _new(tmp_path, stack_name)
    stack = load_stacks()[stack_name]
    pyproject = (project / "pyproject.toml").read_text()
    assert f'requires-python = ">={stack.python_minimum}"' in pyproject
    assert f'target-version = "py{stack.python_minimum.replace(".", "")}"' in pyproject
    assert _matrix(project) == list(stack.python_versions)
    assert "{{" not in pyproject


def test_raising_the_floor_rewrites_every_line_that_names_a_version(tmp_path) -> None:
    project = _new(tmp_path, "python-lib", "--python", "3.12")
    pyproject = (project / "pyproject.toml").read_text()
    assert 'requires-python = ">=3.12"' in pyproject
    assert 'target-version = "py312"' in pyproject
    assert '"Programming Language :: Python :: 3.10"' not in pyproject
    assert '"Programming Language :: Python :: 3.11"' not in pyproject
    assert '"Programming Language :: Python :: 3.12"' in pyproject
    assert _matrix(project) == ["3.12", "3.13"]
    record = json.loads((project / ".newstack.json").read_text())
    assert record["context"]["python_version"] == "3.12"


def test_the_docker_image_follows_the_floor(tmp_path) -> None:
    project = _new(tmp_path, "fastapi", "--python", "3.11")
    assert "FROM python:3.11-slim" in (project / "Dockerfile").read_text()
    assert "Python 3.11" in (project / "README.md").read_text()


def test_a_floor_the_stack_was_not_proven_on_is_refused(tmp_path, capsys) -> None:
    code = main(["new", "python-cli", str(tmp_path / "x"), "--python", "3.9"])
    assert code == 1
    assert "supports Python 3.10, 3.11, 3.12, 3.13" in capsys.readouterr().err
    assert not (tmp_path / "x").exists()


def test_the_stack_minimum_cannot_be_undercut(tmp_path, capsys) -> None:
    code = main(["new", "django", str(tmp_path / "x"), "--python", "3.10"])
    assert code == 1
    assert "supports Python 3.12, 3.13" in capsys.readouterr().err


def test_a_stack_without_a_python_choice_says_so(tmp_path, capsys) -> None:
    code = main(["new", "go-cli", str(tmp_path / "x"), "--python", "3.12"])
    assert code == 1
    assert "has no --python choice" in capsys.readouterr().err


def test_update_keeps_the_recorded_floor(tmp_path, capsys) -> None:
    project = _new(tmp_path, "flask", "--python", "3.11")
    capsys.readouterr()
    assert main(["update", str(project)]) == 0
    assert 'requires-python = ">=3.11"' in (project / "pyproject.toml").read_text()


def test_update_moves_the_floor_when_asked(tmp_path, capsys) -> None:
    project = _new(tmp_path, "flask", "--python", "3.11")
    capsys.readouterr()
    assert main(["update", str(project), "--python", "3.13"]) == 0
    pyproject = (project / "pyproject.toml").read_text()
    assert 'requires-python = ">=3.13"' in pyproject
    assert 'target-version = "py313"' in pyproject
    assert _matrix(project) == ["3.13"]
    record = json.loads((project / ".newstack.json").read_text())
    assert record["context"]["python_version"] == "3.13"


def test_a_project_recorded_before_the_feature_still_updates(tmp_path, capsys) -> None:
    project = _new(tmp_path, "python-cli")
    record_path = project / ".newstack.json"
    record = json.loads(record_path.read_text())
    for key in ("python_version", "python_tag", "python_versions", "python_classifiers"):
        record["context"].pop(key)
    record_path.write_text(json.dumps(record))
    capsys.readouterr()
    assert main(["update", str(project)]) == 0
    assert 'requires-python = ">=3.10"' in (project / "pyproject.toml").read_text()
