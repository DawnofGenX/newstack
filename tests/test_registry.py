from __future__ import annotations

import json
from pathlib import Path

import pytest

from newstack.registry import RegistryError, get_stack, load_stack, load_stacks


def test_every_builtin_stack_loads() -> None:
    stacks = load_stacks()
    assert len(stacks) >= 6
    for name, stack in stacks.items():
        assert stack.name == name
        assert stack.template_dir.is_dir(), name
        assert stack.verify, f"{name} has no verification steps"


def test_get_stack_unknown_lists_alternatives() -> None:
    with pytest.raises(RegistryError, match="unknown stack"):
        get_stack("does-not-exist")


def _manifest(tmp_path: Path, data: dict, dirname: str | None = None) -> Path:
    directory = tmp_path / (dirname or data.get("name", "demo"))
    directory.mkdir()
    (directory / "stack.json").write_text(json.dumps(data), encoding="utf-8")
    (directory / "template").mkdir()
    return directory


BASE = {"name": "demo", "title": "Demo", "language": "python", "blurb": "demo stack"}


def test_manifest_name_must_match_directory(tmp_path) -> None:
    directory = _manifest(tmp_path, {**BASE, "name": "other"}, dirname="demo")
    with pytest.raises(RegistryError, match="must match directory"):
        load_stack(directory)


def test_manifest_rejects_invalid_json(tmp_path) -> None:
    directory = tmp_path / "demo"
    directory.mkdir()
    (directory / "stack.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(RegistryError, match="invalid JSON"):
        load_stack(directory)


def test_manifest_requires_template_directory(tmp_path) -> None:
    directory = _manifest(tmp_path, BASE)
    (directory / "template").rmdir()
    with pytest.raises(RegistryError, match="template"):
        load_stack(directory)


def test_manifest_verify_step_needs_cmd(tmp_path) -> None:
    directory = _manifest(tmp_path, {**BASE, "verify": [{"name": "x"}]})
    with pytest.raises(RegistryError, match="needs a 'cmd'"):
        load_stack(directory)


def test_manifest_parses_verify_steps(tmp_path) -> None:
    directory = _manifest(
        tmp_path,
        {**BASE, "verify": [{"name": "test", "cmd": "pytest", "tools": ["pytest"], "timeout": 42}]},
    )
    stack = load_stack(directory)
    assert stack.verify[0].name == "test"
    assert stack.verify[0].tools == ("pytest",)
    assert stack.verify[0].timeout == 42


def test_env_var_adds_stacks(tmp_path, monkeypatch) -> None:
    external = tmp_path / "external"
    external.mkdir()
    directory = external / "demo"
    directory.mkdir()
    (directory / "stack.json").write_text(json.dumps(BASE), encoding="utf-8")
    (directory / "template").mkdir()
    (directory / "template" / "README.md").write_text("# demo", encoding="utf-8")

    monkeypatch.setenv("NEWSTACK_STACKS", str(external))
    stacks = load_stacks()
    assert "demo" in stacks
    assert "python-lib" in stacks
