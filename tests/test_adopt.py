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
        # go.mod and Cargo.toml each match TWO stacks by design (cli + service), so
        # adopt on a real Go/Rust repo must ask for --stack rather than guess.
        ({"go.mod": "module x\n\ngo 1.24\n"}, ["go-cli", "go-http"]),
        ({"Cargo.toml": '[package]\nname = "x"\n'}, ["rust-cli", "rust-axum"]),
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
    found = sorted(stack.name for stack in detect_stacks(tmp_path))
    assert found == sorted([expected] if isinstance(expected, str) else expected)


def test_a_next_project_is_not_mistaken_for_a_react_spa(tmp_path) -> None:
    # every Next app depends on React, so `"react"` alone cannot tell them apart:
    # next-app-ts keeps the specific marker and react-vite-ts is the fallback.
    make_repo(
        tmp_path,
        {
            "package.json": json.dumps(
                {"dependencies": {"next": "^16", "react": "^19", "react-dom": "^19"}}
            )
        },
    )
    assert [stack.name for stack in detect_stacks(tmp_path)] == ["next-app-ts"]


def test_a_plain_react_project_still_resolves_to_the_vite_spa(tmp_path) -> None:
    make_repo(tmp_path, {"package.json": json.dumps({"dependencies": {"react": "^19"}})})
    assert [stack.name for stack in detect_stacks(tmp_path)] == ["react-vite-ts"]


def test_generic_python_fallback_is_suppressed_by_a_specific_match(tmp_path) -> None:
    make_repo(tmp_path, {"pyproject.toml": 'dependencies = ["django"]\n'})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["django"], "python-lib must not compete with the specific match"


def test_kotlin_pom_is_not_claimed_by_the_java_fallback(tmp_path) -> None:
    """A pom.xml that mentions kotlin must resolve to kotlin-cli alone.

    java-maven-cli detects a bare pom.xml, which would otherwise make every Kotlin/Maven
    project ambiguous; it is a fallback, so a more specific rule wins.
    """

    pom = (
        "<project><artifactId>k</artifactId>"
        "<dependency>kotlin-stdlib</dependency></project>"
    )
    make_repo(tmp_path, {"pom.xml": pom})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["kotlin-cli"], "java-maven-cli must not compete with the specific match"


def test_plain_maven_pom_still_resolves_to_the_java_stack(tmp_path) -> None:
    make_repo(tmp_path, {"pom.xml": "<project><artifactId>plain</artifactId></project>"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["java-maven-cli"], "the java fallback must still catch a plain pom.xml"


def test_a_glob_marker_finds_a_project_named_by_its_build_file(tmp_path) -> None:
    """haskell-cli is marked by `*.cabal`, because the file carries the project name.

    A literal marker cannot express that, so detect rules accept a glob.
    """

    make_repo(tmp_path, {"mytool.cabal": "cabal-version: 3.0\nname: mytool\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["haskell-cli"], "the *.cabal rule must match any cabal package file"


def test_symfony_app_wins_over_the_composer_fallback(tmp_path) -> None:
    """A Symfony project is also a Composer project.

    php-composer-cli detects a bare composer.json; it is a fallback, so the more specific
    `bin/console` marker must decide, or every Symfony repo exits 2 as ambiguous.
    """

    make_repo(
        tmp_path,
        {
            "composer.json": '{"require": {"symfony/framework-bundle": "^7.3"}}',
            "bin/console": "#!/usr/bin/env php\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["symfony-app"], "php-composer-cli must not compete with a Symfony project"


def test_laravel_app_wins_over_the_composer_fallback(tmp_path) -> None:
    """A Laravel project is also a Composer project.

    php-composer-cli detects a bare composer.json; it is a fallback, so the more specific
    `artisan` marker must decide, or a Laravel repo exits 2 as ambiguous.
    """

    make_repo(
        tmp_path,
        {
            "composer.json": '{"require": {"laravel/framework": "^13.17"}}',
            "artisan": "#!/usr/bin/env php\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["laravel-app"], "php-composer-cli must not compete with a Laravel project"


def test_plain_composer_project_still_resolves_to_php_composer_cli(tmp_path) -> None:
    make_repo(tmp_path, {"composer.json": '{"require": {"php": "^8.3"}}'})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["php-composer-cli"], "the composer fallback must still catch a plain package"


def test_aspnet_api_wins_over_the_dotnet_fallback(tmp_path) -> None:
    """An ASP.NET project is also a .NET project.

    dotnet-cli matches any `*.csproj`; it is a fallback, so the Web SDK marker on the
    project file must decide, or every web API exits 2 as ambiguous.
    """

    make_repo(
        tmp_path,
        {"Stats.Api.csproj": '<Project Sdk="Microsoft.NET.Sdk.Web">\n</Project>\n'},
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["aspnet-api"], "dotnet-cli must not compete with a web project"


def test_plain_console_project_still_resolves_to_dotnet_cli(tmp_path) -> None:
    make_repo(tmp_path, {"tool.csproj": '<Project Sdk="Microsoft.NET.Sdk">\n</Project>\n'})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["dotnet-cli"], "the csproj fallback must still catch a console project"


def test_phoenix_app_wins_over_the_mix_fallback(tmp_path) -> None:
    """A Phoenix project is also a Mix project.

    elixir-mix-cli detects a bare mix.exs; it is a fallback, so the `:phoenix`
    dependency in that same file must decide, or every Phoenix repo is ambiguous.
    """

    make_repo(
        tmp_path,
        {
            "mix.exs": (
                "defmodule Demo.MixProject do\n"
                "  defp deps, do: [{:phoenix, \"~> 1.7\"}]\n"
                "end\n"
            )
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["phoenix-app"], "elixir-mix-cli must not compete with a Phoenix project"


def test_plain_mix_project_still_resolves_to_elixir_mix_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {"mix.exs": 'defmodule Demo.MixProject do\n  defp deps, do: [{:jason, "~> 1.4"}]\nend\n'},
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["elixir-mix-cli"], "the mix fallback must still catch a plain project"


def test_an_action_repository_is_recognised_by_action_yml(tmp_path) -> None:
    """`action.yml` is the only marker a GitHub Action repository needs."""

    make_repo(tmp_path, {"action.yml": "name: measure\nruns:\n  using: node24\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["github-action"]


def test_a_c11_makefile_resolves_to_the_c_stack(tmp_path) -> None:
    """`-std=c11` is the marker: the other Makefile stacks name their own compiler."""

    make_repo(
        tmp_path,
        {
            "Makefile": (
                "CFLAGS := -std=c11 -O2 -Wall -Wextra -Werror\n"
                "all:\n"
                "\tcc -o app src/main.c\n"
            ),
            "src/main.c": "int main(void) { return 0; }\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["c-cli"], "a plain C Makefile must not look like Pascal/COBOL/Fortran"


def test_unrecognised_directory_yields_no_candidates(tmp_path) -> None:
    (tmp_path / "notes.txt").write_text("nothing here")
    assert detect_stacks(tmp_path) == []


def test_two_specific_matches_are_reported_as_ambiguous(tmp_path) -> None:
    # go.mod matches the CLI and the HTTP service; neither is a fallback, so the
    # only honest answer is to ask which one this repository is.
    make_repo(tmp_path, {"go.mod": "module x\n\ngo 1.24\n"})
    names = sorted(stack.name for stack in detect_stacks(tmp_path))
    assert names == ["go-cli", "go-http"]


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
    make_repo(tmp_path, {"index.html": "<!doctype html><html></html>"})
    assert main(["adopt", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "static-site (auto-detected)" in out
    assert (tmp_path / ".github/workflows/deploy-pages.yml").is_file()


def test_cli_adopt_dry_run_writes_nothing(tmp_path, capsys) -> None:
    make_repo(tmp_path, {"index.html": "<!doctype html><html></html>"})
    assert main(["adopt", str(tmp_path), "--dry-run"]) == 0
    assert "would add" in capsys.readouterr().out
    assert not (tmp_path / ".github").exists()


def test_cli_adopt_json_schema(tmp_path, capsys) -> None:
    make_repo(tmp_path, {"index.html": "<!doctype html><html></html>"})
    assert main(["adopt", str(tmp_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["stack"] == "static-site"
    assert payload["added"]
    assert payload["dry_run"] is False


def test_cli_adopt_ambiguous_exits_2(tmp_path, capsys) -> None:
    make_repo(tmp_path, {"go.mod": "module x\n\ngo 1.24\n"})
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
    make_repo(tmp_path, {"index.html": "<!doctype html><html></html>"})
    assert main(["adopt", str(tmp_path), "--with-tests"]) == 0
    assert (tmp_path / "tests/site.test.mjs").is_file()


def test_cli_adopt_without_flag_skips_tests(tmp_path) -> None:
    make_repo(tmp_path, {"index.html": "<!doctype html><html></html>"})
    assert main(["adopt", str(tmp_path)]) == 0
    assert not (tmp_path / "tests/site.test.mjs").exists()


def test_cli_adopt_is_idempotent(tmp_path, capsys) -> None:
    make_repo(tmp_path, {"index.html": "<!doctype html><html></html>"})
    assert main(["adopt", str(tmp_path)]) == 0
    first = (tmp_path / ".github/workflows/deploy-pages.yml").read_bytes()
    assert main(["adopt", str(tmp_path)]) == 0
    assert "the infrastructure files are already present" in capsys.readouterr().out
    assert (tmp_path / ".github/workflows/deploy-pages.yml").read_bytes() == first


def test_cli_adopt_go_repo_asks_for_stack(tmp_path, capsys) -> None:
    """A Go repo matches both go-cli and go-http: adopt must ask, never guess."""
    make_repo(tmp_path, {"go.mod": "module demo\n"})
    assert main(["adopt", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert "go-cli" in err and "go-http" in err


def test_a_tsup_package_resolves_to_the_ts_library_stack(tmp_path) -> None:
    """`tsup` in devDependencies is the marker for a bundled library.

    Application stacks detect package.json too, but they look for their own framework
    dependency, so a package that bundles itself is unambiguous.
    """

    make_repo(
        tmp_path,
        {
            "package.json": (
                '{"name": "demo",\n'
                ' "devDependencies": {"tsup": "^9.0.0", "vitest": "^5.1.0"}}\n'
            ),
            "src/index.ts": "export const answer = 42;\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["ts-lib"]


def test_a_hono_package_resolves_to_the_hono_stack(tmp_path) -> None:
    """`hono` in dependencies is the marker; the app stacks look for their own framework."""

    make_repo(
        tmp_path,
        {
            "package.json": (
                '{"name": "demo",\n'
                ' "dependencies": {"hono": "^4.13.16", "@hono/node-server": "^2.1.6"}}\n'
            ),
            "src/app.ts": 'export const app = 1;\n',
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["hono-api"]


def test_a_sphinx_conf_resolves_to_the_docs_stack(tmp_path) -> None:
    """`docs/conf.py` is the marker: a package with no docs/conf.py is a package, not a site."""

    make_repo(
        tmp_path,
        {
            "docs/conf.py": 'project = "demo"\nextensions = ["sphinx.ext.autodoc"]\n',
            "docs/index.rst": "demo\n====\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["sphinx-docs"]


def test_an_openapi_document_resolves_to_the_contract_stack(tmp_path) -> None:
    """`openapi.yaml` is the marker; a package.json alone must not shadow it."""

    make_repo(
        tmp_path,
        {
            "openapi.yaml": 'openapi: 3.1.0\ninfo:\n  title: demo\n  version: 0.1.0\n',
            "package.json": '{"name": "demo"}\n',
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["openapi-spec"]
