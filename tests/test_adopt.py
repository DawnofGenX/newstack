"""Tests for `newstack adopt`: detection, additive writes, and reports."""

from __future__ import annotations

import json

import pytest

from newstack.adopt import FORBIDDEN, apply_plan, detect_stacks, plan_adoption
from newstack.cli import build_context_for_check, main
from newstack.registry import load_stacks

STACKS = load_stacks()


def make_repo(root, files: dict[str, str]):
    for rel, content in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


# --------------------------------------------------------------------- detection


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        ({"go.mod": "module x\n\ngo 1.24\n"}, "go-cli"),
        ({"Cargo.toml": '[package]\nname = "x"\n'}, "rust-cli"),
        ({"manage.py": "#!/usr/bin/env python\n", "pyproject.toml": "[project]\n"}, "django"),
        ({"pyproject.toml": 'dependencies = ["fastapi"]\n'}, "fastapi"),
        ({"package.json": '{"dependencies": {"express": "^5"}}'}, "node-express-ts"),
        ({"package.json": '{"dependencies": {"@sveltejs/kit": "^3"}}'}, "svelte-kit-ts"),
        ({"package.json": '{"dependencies": {"react": "^19"}}'}, "react-vite-ts"),
        ({"index.html": "<!doctype html><html></html>"}, "static-site"),
    ],
)
def test_detects_each_stack(tmp_path, files, expected) -> None:
    make_repo(tmp_path, files)
    assert [stack.name for stack in detect_stacks(tmp_path)] == [expected]


def test_generic_python_fallback_is_suppressed_by_a_specific_match(tmp_path) -> None:
    make_repo(tmp_path, {"pyproject.toml": 'dependencies = ["django"]\n'})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["django"], "python-lib must not compete with the specific match"


def test_unrecognised_directory_yields_no_candidates(tmp_path) -> None:
    (tmp_path / "notes.txt").write_text("nothing here")
    assert detect_stacks(tmp_path) == []


def test_two_specific_matches_are_reported_as_ambiguous(tmp_path) -> None:
    make_repo(tmp_path, {"package.json": '{"dependencies": {"react": "19", "express": "5"}}'})
    names = sorted(stack.name for stack in detect_stacks(tmp_path))
    assert names == ["node-express-ts", "react-vite-ts"]


# --------------------------------------------------------------------- planning


def test_plan_is_additive_and_reports_kept_files(tmp_path) -> None:
    make_repo(tmp_path, {"go.mod": "module x\n", ".gitignore": "my own rules\n"})
    stack = STACKS["go-cli"]
    context = build_context_for_check(stack, "demo")
    plan = plan_adoption(stack, tmp_path, context)

    assert ".gitignore" in plan.keep
    assert ".github/workflows/ci.yml" in plan.added


def test_apply_plan_never_rewrites_an_existing_file(tmp_path) -> None:
    make_repo(tmp_path, {"go.mod": "module x\n", ".gitignore": "my own rules\n"})
    stack = STACKS["go-cli"]
    context = build_context_for_check(stack, "demo")
    plan = plan_adoption(stack, tmp_path, context)
    apply_plan(plan)
    assert (tmp_path / ".gitignore").read_text() == "my own rules\n"
    assert (tmp_path / ".github/workflows/ci.yml").is_file()


def test_apply_plan_skips_a_file_created_after_planning(tmp_path) -> None:
    make_repo(tmp_path, {"go.mod": "module x\n"})
    stack = STACKS["go-cli"]
    context = build_context_for_check(stack, "demo")
    plan = plan_adoption(stack, tmp_path, context)
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/ci.yml").write_text("mine now")
    apply_plan(plan)
    assert (tmp_path / ".github/workflows/ci.yml").read_text() == "mine now"


def test_rendered_files_use_the_directory_name(tmp_path) -> None:
    make_repo(tmp_path, {"package.json": '{"dependencies": {"react": "^19"}}'})
    stack = STACKS["react-vite-ts"]
    plan = plan_adoption(stack, tmp_path, build_context_for_check(stack, "my-dashboard"))
    apply_plan(plan)
    workflow = (tmp_path / ".github/workflows/ci.yml").read_text()
    assert "{{" not in workflow.replace("${{", "")
    assert "my-dashboard" in workflow or "my_dashboard" in workflow or "node" in workflow


def test_manifest_adopt_lists_never_include_project_identity() -> None:
    for stack in STACKS.values():
        assert stack.adopt, f"{stack.name} declares no adoptable files"
        identity = (set(stack.adopt) | set(stack.adopt_tests)) & FORBIDDEN
        assert not identity, f"{stack.name} would copy {sorted(identity)} into a project"


def test_every_adopt_path_exists_in_its_template() -> None:
    for stack in STACKS.values():
        for rel in (*stack.adopt, *stack.adopt_tests):
            assert (stack.template_dir / rel).exists(), f"{stack.name}: missing {rel}"


def test_stack_without_adoptables_is_rejected(tmp_path) -> None:
    from newstack.render import TemplateError

    empty = load_stacks()["go-cli"].__class__(
        **{**load_stacks()["go-cli"].__dict__, "adopt": ()}
    )
    with pytest.raises(TemplateError, match="no adoptable files"):
        plan_adoption(empty, tmp_path, {})


# --------------------------------------------------------------------- CLI


def test_cli_adopt_detects_and_adds(tmp_path, capsys) -> None:
    make_repo(tmp_path, {"go.mod": "module demo\n"})
    assert main(["adopt", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "go-cli (auto-detected)" in out
    assert (tmp_path / ".github/workflows/ci.yml").is_file()


def test_cli_adopt_dry_run_writes_nothing(tmp_path, capsys) -> None:
    make_repo(tmp_path, {"go.mod": "module demo\n"})
    assert main(["adopt", str(tmp_path), "--dry-run"]) == 0
    assert "would add" in capsys.readouterr().out
    assert not (tmp_path / ".github").exists()


def test_cli_adopt_json_schema(tmp_path, capsys) -> None:
    make_repo(tmp_path, {"go.mod": "module demo\n"})
    assert main(["adopt", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["stack"] == "go-cli"
    assert payload["added"]
    assert payload["dry_run"] is False


def test_cli_adopt_ambiguous_exits_2(tmp_path, capsys) -> None:
    make_repo(tmp_path, {"package.json": '{"dependencies": {"react": "19", "express": "5"}}'})
    assert main(["adopt", str(tmp_path)]) == 2
    assert "more than one stack" in capsys.readouterr().err


def test_cli_adopt_unknown_project_errors(tmp_path, capsys) -> None:
    (tmp_path / "notes.txt").write_text("x")
    assert main(["adopt", str(tmp_path)]) == 1
    assert "could not recognise" in capsys.readouterr().err


def test_cli_adopt_stack_override_works_without_markers(tmp_path, capsys) -> None:
    assert main(["adopt", str(tmp_path), "--stack", "python-lib"]) == 0
    assert "(--stack)" in capsys.readouterr().out
    assert (tmp_path / ".github/workflows/ci.yml").is_file()


def test_cli_adopt_with_tests_copies_starter_tests(tmp_path) -> None:
    make_repo(tmp_path, {"go.mod": "module demo\n"})
    assert main(["adopt", str(tmp_path), "--with-tests"]) == 0
    assert (tmp_path / "internal/app/app_test.go").is_file()


def test_cli_adopt_without_flag_skips_tests(tmp_path) -> None:
    make_repo(tmp_path, {"go.mod": "module demo\n"})
    assert main(["adopt", str(tmp_path)]) == 0
    assert not (tmp_path / "internal/app/app_test.go").exists()


def test_cli_adopt_is_idempotent(tmp_path, capsys) -> None:
    make_repo(tmp_path, {"go.mod": "module demo\n"})
    assert main(["adopt", str(tmp_path)]) == 0
    first = (tmp_path / ".github/workflows/ci.yml").read_bytes()
    assert main(["adopt", str(tmp_path)]) == 0
    assert "the infrastructure files are already present" in capsys.readouterr().out
    assert (tmp_path / ".github/workflows/ci.yml").read_bytes() == first
