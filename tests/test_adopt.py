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

STACK_LIST = sorted(STACKS.values(), key=lambda stack: stack.name)


def _path_for(pattern: str):
    """A concrete file path a glob rule can match, with the glob part filled in."""
    parts = []
    for part in pattern.split("/"):
        if part == "**":
            parts.append("src")
        else:
            parts.append(part.replace("*", "marker").replace("?", "m"))
    return "/".join(parts)


@pytest.mark.parametrize("stack", STACK_LIST, ids=[stack.name for stack in STACK_LIST])
def test_every_stack_recognises_its_own_marker(stack, tmp_path):
    """Each stack's detect rules must be satisfied by a directory built from them.

    This is the guard the registry kept missing: a stack whose marker is shared
    with another stack (``go.mod``, a bare ``Makefile``) still has to come out of
    `detect_stacks` when its own evidence is present, and a *specific* stack must
    not be shadowed by a fallback that matches everything.
    """
    assert stack.detect, f"{stack.name} ships no detect rule at all"
    for rule in stack.detect:
        target = tmp_path / _path_for(rule.file)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rule.contains or "marker\n", encoding="utf-8")

    names = [match.name for match in detect_stacks(tmp_path)]
    assert stack.name in names, (
        f"{stack.name} does not recognise a directory built from its own markers; got {names}"
    )



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


def test_a_yoga_package_resolves_to_the_graphql_stack(tmp_path) -> None:
    """`graphql-yoga` is the marker; the schema-first server is what the stack owns."""

    make_repo(
        tmp_path,
        {
            "package.json": (
                '{"name": "demo",\n'
                ' "dependencies": {"graphql": "^17.1.0", "graphql-yoga": "^6.0.1"}}\n'
            ),
            "src/yoga.ts": "export const yoga = 1;\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["graphql-api"]


def test_a_plain_graphql_dependency_is_not_enough(tmp_path) -> None:
    """`graphql` alone is a library, not a server: only the Yoga runtime marks this stack."""

    make_repo(
        tmp_path,
        {"package.json": '{"name": "demo", "dependencies": {"graphql": "^17.1.0"}}\n'},
    )
    assert [stack.name for stack in detect_stacks(tmp_path)] == []


def test_a_dbt_project_resolves_to_the_dbt_stack(tmp_path) -> None:
    """`dbt_project.yml` is the marker; the SQL under models/ is what the stack owns."""

    make_repo(
        tmp_path,
        {
            "dbt_project.yml": "name: demo\nversion: '0.1.0'\nconfig-version: 2\n",
            "models/marts/doc_stats.sql": "select 1 as id\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["dbt-project"]


def test_a_buf_workspace_resolves_to_the_grpc_stack(tmp_path) -> None:
    """`buf.yaml` is the marker: a protobuf module is a contract, not just a Go binary."""

    make_repo(
        tmp_path,
        {
            "go.mod": "module example.com/demo\n\ngo 1.24\n",
            "buf.yaml": "version: v2\nmodules:\n  - path: proto\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["go-cli", "go-http", "grpc-go"]


def test_a_buf_workspace_without_go_still_resolves(tmp_path) -> None:
    """The contract is the marker on its own; the Go toolchain comes from requirements."""

    make_repo(tmp_path, {"buf.yaml": "version: v2\n"})
    assert [stack.name for stack in detect_stacks(tmp_path)] == ["grpc-go"]


def test_a_shelf_pubspec_resolves_to_the_dart_service(tmp_path) -> None:
    """`shelf` in the dependencies is what separates a service from a plain Dart CLI."""

    make_repo(
        tmp_path,
        {
            "pubspec.yaml": (
                'name: demo\nenvironment:\n  sdk: ">=3.5.0 <4.0.0"\n'
                "dependencies:\n  shelf: ^1.4.2\n  shelf_router: ^1.1.4\n"
            )
        },
    )
    assert [stack.name for stack in detect_stacks(tmp_path)] == ["dart-shelf-api"]


def test_a_plain_pubspec_still_resolves_to_the_dart_cli(tmp_path) -> None:
    """The service detects a narrower marker, so the CLI stack has to stay the fallback."""

    make_repo(
        tmp_path,
        {"pubspec.yaml": 'name: demo\nenvironment:\n  sdk: ">=3.5.0 <4.0.0"\n'},
    )
    assert [stack.name for stack in detect_stacks(tmp_path)] == ["dart-cli"]


def test_a_deno_config_with_std_http_resolves_to_the_deno_service(tmp_path) -> None:
    """`@std/http` in the import map means a server, not a script runner."""

    make_repo(
        tmp_path,
        {
            "deno.json": '{"imports": {"@std/http": "jsr:@std/http@^1.0.0"}}',
            "src/server.ts": "Deno.serve(handler);\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["deno-api"]


def test_a_plain_deno_config_still_resolves_to_the_deno_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "deno.json": '{"imports": {"@std/assert": "jsr:@std/assert@^1.0.0"}}',
            "src/main.ts": "console.log('hi');\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["deno-cli"]


def test_a_bun_package_resolves_to_the_bun_service(tmp_path) -> None:
    """`bun-types` in devDependencies means the project is type-checked against Bun itself."""

    make_repo(
        tmp_path,
        {
            "package.json": '{"devDependencies": {"bun-types": "^1.4.4"}}',
            "src/server.ts": "Bun.serve({ fetch: handler });\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["bun-api"]


def test_a_bunfig_file_still_resolves_to_the_bun_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {".bunfig.toml": '[test]\nroot = "."\n', "src/cli.ts": "export {};\n"},
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["bun-cli"]


def test_a_ring_deps_file_resolves_to_the_clojure_service(tmp_path) -> None:
    """`ring/ring-core` in `deps.edn` means a server, not a script runner."""

    make_repo(
        tmp_path,
        {
            "deps.edn": '{:deps {ring/ring-core {:mvn/version "1.15.0"}}}\n',
            "src/demo/handler.clj": "(ns demo.handler)\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["clojure-ring-api"]


def test_a_plain_deps_file_still_resolves_to_the_clojure_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "deps.edn": '{:deps {org.clojure/clojure {:mvn/version "1.12.6"}}}\n',
            "src/textstat/cli.clj": "(ns textstat.cli)\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["clojure-cli"]



def test_a_nim_server_resolves_to_the_nim_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "blog_count.nimble": 'version = "0.1.0"\nrequires "nim >= 1.6.0"\n',
            "src/server.nim": "import std/asynchttpserver\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["nim-http-api"]


def test_a_plain_nim_project_still_resolves_to_the_nim_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "blog_count.nimble": 'version = "0.1.0"\nrequires "nim >= 1.6.0"\n',
            "nim.cfg": "--path:src\n",
            "src/blog_count.nim": "echo \"hello\"\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["nim-cli"]


def test_a_kemal_shard_resolves_to_the_crystal_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "shard.yml": 'name: blog_count\ncrystal: ">= 1.11.0"\ndependencies:\n  kemal:\n'
            "    github: kemalcr/kemal\n",
            "src/blog_count/main.cr": "require \"./server\"\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["crystal-kemal-api"]


def test_a_plain_shard_still_resolves_to_the_crystal_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "shard.yml": 'name: textstat\ncrystal: ">= 1.11.0"\n',
            "src/textstat.cr": "puts \"hello\"\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["crystal-cli"]

def test_a_mist_gleam_config_resolves_to_the_gleam_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "gleam.toml": 'name = "blog_count"\ntarget = "erlang"\n\n[dependencies]\n'
            'mist = ">= 6.0.0 and < 7.0.0"\n',
            "src/blog_count.gleam": "pub fn main() { Nil }\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["gleam-mist-api"]


def test_a_luasocket_service_resolves_to_the_lua_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            ".luarc.json": '{"runtime.version": "Lua 5.4"}\n',
            "src/server.lua": (
                'local socket = require("socket")\n'
                "local server = assert(socket.bind(\"127.0.0.1\", 8080))\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["lua-http-api"]


def test_the_lua_cli_still_resolves_without_a_socket(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            ".luarc.json": '{"runtime.version": "Lua 5.4"}\n',
            "src/counts.lua": (
                "local M = {}\n\nfunction M.count(text) return #text end\n\nreturn M\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["lua-cli"]


def test_a_plain_gleam_config_still_resolves_to_the_gleam_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "gleam.toml": 'name = "blog_count"\ntarget = "erlang"\n\n[dependencies]\n'
            'gleam_stdlib = ">= 1.0.0 and < 2.0.0"\n',
            "src/blog_count.gleam": "pub fn main() { Nil }\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["gleam-cli"]


def test_a_cask_scala_project_resolves_to_the_scala_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "project.scala": "//> using scala 3.3.7\n"
            "//> using dep com.lihaoyi::cask:0.11.3\n",
            "src/blog_count/Server.scala": "package blog_count\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["scala-cask-api"]


def test_a_plain_scala_project_still_resolves_to_the_scala_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "project.scala": "//> using scala 3.3.7\n//> using dep com.lihaoyi::os-lib:0.11.3\n",
            "src/Main.scala": "object Main { def main(args: Array[String]): Unit = () }\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["scala-cli"]


def test_a_zig_server_resolves_to_the_zig_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "build.zig.zon": '.{ .name = .textstat, .version = "0.1.0" }\n',
            "build.zig": "pub fn build(b: *std.Build) void {}\n",
            "src/server.zig": "const std = @import(\"std\");\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["zig-http-api"]


def test_a_plain_zig_package_still_resolves_to_the_zig_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "build.zig.zon": '.{ .name = .textstat, .version = "0.1.0" }\n',
            "build.zig": "pub fn build(b: *std.Build) void {}\n",
            "src/main.zig": "const std = @import(\"std\");\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["zig-cli"]



def test_a_julia_web_project_resolves_to_the_julia_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "Project.toml": 'name = "BlogApi"\n\n[deps]\n'
            'HTTP = "cd3eb016-35fb-5094-929b-558a96fad6f3"\n',
            "src/BlogApi.jl": "module BlogApi\nend\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["julia-api"]


def test_a_plain_julia_project_still_resolves_to_the_julia_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            # `julia-cli` matches any Project.toml that mentions julia, e.g. a compat entry
            "Project.toml": 'name = "Textstat"\n\n[deps]\n\n[compat]\njulia = "1.6"\n',
            "src/Textstat.jl": "module Textstat\nend\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["julia-cli"]



def test_an_mkdocs_config_resolves_to_the_mkdocs_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "mkdocs.yml": "site_name: Docs\nnav:\n  - Home: index.md\n",
            "docs/index.md": "# Docs\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["mkdocs-site"]


def test_a_plumber_entry_file_resolves_to_the_r_service(tmp_path) -> None:
    """plumber.R is the conventional entry point, and nothing else uses that name."""
    make_repo(tmp_path, {"plumber.R": "#* @get /health\nfunction() list(status = 'ok')\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["r-plumber-api"]


def test_a_plumber_project_with_a_description_still_resolves_to_the_service(tmp_path) -> None:
    """r-cli detects a DESCRIPTION, so it is a fallback: the service must still win."""
    make_repo(
        tmp_path,
        {
            "plumber.R": "#* @get /health\nfunction() list(status = 'ok')\n",
            "DESCRIPTION": "Package: blogcount\nTitle: x\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["r-plumber-api"], "the service marker is the specific one"


def test_a_plain_r_package_still_resolves_to_the_r_cli(tmp_path) -> None:
    make_repo(tmp_path, {"DESCRIPTION": "Package: blogcount\nTitle: x\n", "R/counts.R": "x <- 1\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["r-cli"], "a package with no entry point is the CLI stack"


def test_a_cowboy_rebar_config_resolves_to_the_erlang_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "rebar.config": "{deps, [{cowboy, \"2.13.0\"}]}.\n",
            "src/blog_count_app.erl": "-module(blog_count_app).\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["erlang-cowboy-api"]


def test_a_rebar_project_without_cowboy_is_not_claimed_by_the_service(tmp_path) -> None:
    """rebar.config alone says nothing about a web service, and erlang-cli is Makefile-based."""
    make_repo(tmp_path, {"rebar.config": "{deps, [{jsx, \"3.1.0\"}]}.\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == []


def test_a_mojolicious_cpanfile_resolves_to_the_perl_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "cpanfile": "requires 'Mojolicious', '>= 9.30';\n",
            "lib/Textstat/Contract.pm": "package Textstat::Contract;\n1;\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["perl-mojolicious-api"], "the web dependency picks the service"


def test_a_plain_perl_project_still_resolves_to_the_perl_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "Makefile.PL": "use ExtUtils::MakeMaker;\nWriteMakefile(NAME => 'Textstat');\n",
            "lib/Textstat.pm": "package Textstat;\n1;\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["perl-cli"], "a distribution with no web dependency is the CLI stack"


def test_a_warp_cabal_file_resolves_to_the_haskell_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "blog-count.cabal": "name: blog-count\nbuild-depends: base, warp\n",
            "src/Contract.hs": "module Contract where\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["haskell-warp-api"], "warp in the cabal file is the service marker"


def test_a_plain_cabal_project_still_resolves_to_the_haskell_cli(tmp_path) -> None:
    make_repo(tmp_path, {"blog-count.cabal": "name: blog-count\nbuild-depends: base\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["haskell-cli"], "cabal without warp is the CLI stack"


def test_a_racket_web_server_resolves_to_the_racket_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "src/server.rkt": '#lang racket/base\n(require web-server/servlet-env)\n',
            "src/counts.rkt": "#lang racket/base\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["racket-api"], "the web server require is the service marker"


def test_a_plain_racket_script_still_resolves_to_the_racket_cli(tmp_path) -> None:
    make_repo(tmp_path, {"main.rkt": '#lang racket/base\n(displayln 1)\n'})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["racket-cli"], "a script with no web server is the CLI stack"


def test_a_prolog_http_server_resolves_to_the_prolog_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "src/server.pl": (
                ":- use_module(library(http/http_dispatch)).\n"
                ":- use_module(library(http/thread_httpd)).\n"
            )
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["prolog-http-api"], "http_dispatch is the service marker"


def test_a_plain_prolog_script_still_resolves_to_the_prolog_cli(tmp_path) -> None:
    make_repo(tmp_path, {"main.pl": ":- initialization(main, main).\nmain :- writeln(hi).\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["prolog-cli"], "a script with no http library is the CLI stack"


def test_a_http_listener_script_resolves_to_the_powershell_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {"src/server.ps1": "$listener = [System.Net.HttpListener]::new()\n$listener.Start()\n"},
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["powershell-api"], "HttpListener is the service marker"


def test_a_plain_powershell_script_still_resolves_to_the_powershell_cli(tmp_path) -> None:
    make_repo(tmp_path, {"main.ps1": "Write-Output 'hello'\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["powershell-cli"], "a script with no listener is the CLI stack"


def test_a_guile_web_server_resolves_to_the_guile_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "src/server.scm": "(use-modules (web server))\n(display \"hello\")\n",
            "lib/textstat/counts.scm": "(define-module (textstat counts))\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["guile-http-api"], "(web server) is the service marker"


def test_a_plain_guile_script_still_resolves_to_the_guile_cli(tmp_path) -> None:
    make_repo(tmp_path, {"main.scm": "(display \"hello\")\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["guile-cli"], "a script with no web server is the CLI stack"


def test_a_tcl_socket_server_resolves_to_the_tcl_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "src/server.tcl": "socket -server textstat::server::handle 0\n",
            "src/counts.tcl": "proc textstat::counts::count_text {text} { return $text }\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["tcl-http-api"], "socket -server is the service marker"


def test_a_plain_tcl_script_still_resolves_to_the_tcl_cli(tmp_path) -> None:
    make_repo(tmp_path, {"main.tcl": "puts \"hello\"\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["tcl-cli"], "a script with no socket is the CLI stack"


def test_a_raku_socket_server_resolves_to_the_raku_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "lib/Server.rakumod": (
                "unit module Server;\n"
                "my $listener = IO::Socket::INET.new(:listen, :localport(0));\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["raku-http-api"], "IO::Socket::INET is the service marker"


def test_a_plain_raku_script_still_resolves_to_the_raku_cli(tmp_path) -> None:
    make_repo(tmp_path, {"main.raku": "say \"hello\";\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["raku-cli"], "a script with no socket is the CLI stack"


def test_a_lisp_socket_server_resolves_to_the_lisp_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "main.lisp": '(format t "hello")',
            "lib/server.lisp": "(require :sb-bsd-sockets)\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["lisp-http-api"], "sb-bsd-sockets is the service marker"


def test_a_plain_lisp_script_still_resolves_to_the_lisp_cli(tmp_path) -> None:
    make_repo(tmp_path, {"main.lisp": '(format t "hello")'})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["lisp-cli"], "a script that opens no socket is the CLI stack"

def test_a_c_socket_server_resolves_to_the_c_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "Makefile": "all:\n\tcc -std=c11 -o app src/main.c\n",
            "src/http.c": "int s = socket(AF_INET, SOCK_STREAM, 0);\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["c-http-api"], "SOCK_STREAM is the service marker"


def test_a_plain_c_project_still_resolves_to_the_c_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "Makefile": "all:\n\tcc -std=c11 -o app src/main.c\n",
            "src/main.c": "int main(void) { return 0; }\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["c-cli"], "a Makefile with -std=c11 and no socket is the CLI stack"

def test_a_d_socket_server_resolves_to_the_d_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "source/app.d": "void main() {}\n",
            "source/textstat/server.d": "import std.socket;\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["d-http-api"], "std.socket is the service marker"


def test_a_plain_d_project_still_resolves_to_the_d_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "source/app.d": "void main() {}\n",
            "source/textstat/counts.d": "module textstat.counts;\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["d-cli"], "source/app.d with no socket is the CLI stack"

def test_an_ocaml_socket_server_resolves_to_the_ocaml_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "dune-project": "(lang dune 3.14)\n",
            "lib/server.ml": "let socket = Unix.socket Unix.PF_INET Unix.SOCK_STREAM 0\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["ocaml-http-api"], "Unix.socket is the service marker"


def test_a_plain_ocaml_project_still_resolves_to_the_ocaml_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "dune-project": "(lang dune 3.14)\n",
            "lib/counts.ml": "let of_bytes data = String.length data\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["ocaml-cli"], "a dune project with no socket is the CLI stack"

def test_a_groovy_http_server_resolves_to_the_groovy_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "src/textstat/Server.groovy": "import com.sun.net.httpserver.HttpServer\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["groovy-http-api"], "HttpServer is the service marker"


def test_a_plain_groovy_script_still_resolves_to_the_groovy_cli(tmp_path) -> None:
    make_repo(tmp_path, {"Main.groovy": "println 'hi'\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["groovy-cli"], "a root groovy script with no server is the CLI stack"

def test_a_cpp_socket_server_resolves_to_the_cpp_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "src/http.cpp": "#include <sys/socket.h>\nint main() { return 0; }\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["cpp-http-api"], "sys/socket.h is the service marker"


def test_a_plain_cmake_project_still_resolves_to_the_cmake_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "CMakeLists.txt": "project(tool)\n",
            "src/main.cpp": "int main() { return 0; }\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["cpp-cmake-cli"], "a CMake tree with no socket is the CLI stack"


def test_a_haxe_socket_server_resolves_to_the_haxe_service(tmp_path):
    make_repo(
        tmp_path,
        {
            "build.hxml": "-cp src\n--main textstat.App\n",
            "src/textstat/Server.hx": "import sys.net.Socket;\nclass Server {}\n",
        },
    )
    assert [stack.name for stack in detect_stacks(tmp_path)] == ["haxe-http-api"]


def test_a_plain_haxe_project_still_resolves_to_the_haxe_cli(tmp_path):
    make_repo(
        tmp_path,
        {
            "build.hxml": "-cp src\n--main Main\n",
            "src/Main.hx": "class Main { static function main() {} }\n",
        },
    )
    assert [stack.name for stack in detect_stacks(tmp_path)] == ["haxe-cli"]



def test_a_pascal_http_server_resolves_to_the_pascal_service(tmp_path):
    make_repo(
        tmp_path,
        {
            "Makefile": "FPC ?= fpc\nall:\n\t$(FPC) src/app.pas\n",
            "src/server.pas": "uses fphttpserver;\n",
        },
    )
    assert [stack.name for stack in detect_stacks(tmp_path)] == ["pascal-http-api"]


def test_a_plain_pascal_project_still_resolves_to_the_pascal_cli(tmp_path):
    make_repo(
        tmp_path,
        {
            "Makefile": "FPC ?= fpc\nall:\n\t$(FPC) src/app.pas\n",
            "src/app.pas": "program app;\nbegin\nend.\n",
        },
    )
    assert [stack.name for stack in detect_stacks(tmp_path)] == ["pascal-cli"]


def test_an_ada_socket_server_resolves_to_the_ada_service(tmp_path):
    make_repo(
        tmp_path,
        {
            "Makefile": "all:\n\tgnatmake src/app.adb\n",
            "src/textstat-server.adb": "with GNAT.Sockets;\n",
        },
    )
    assert [stack.name for stack in detect_stacks(tmp_path)] == ["ada-http-api"]


def test_a_plain_ada_project_still_resolves_to_the_ada_cli(tmp_path):
    make_repo(
        tmp_path,
        {
            "Makefile": "all:\n\tgnatmake src/app.adb\n",
            "src/app.adb": "procedure App is begin null; end App;\n",
        },
    )
    assert [stack.name for stack in detect_stacks(tmp_path)] == ["ada-cli"]


def test_a_jdk_http_server_resolves_to_the_java_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "src/main/java/demo/Server.java": (
                "import com.sun.net.httpserver.HttpServer;\nclass Server {}\n"
            )
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["java-httpserver-api"], "com.sun.net.httpserver marks the java service"


def test_plain_java_without_the_jdk_server_stays_a_maven_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "pom.xml": "<project><artifactId>plain</artifactId></project>",
            "src/main/java/demo/App.java": "class App {}\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["java-maven-cli"], "the java service rule must need its own marker"


def test_a_swift_socket_server_resolves_to_the_swift_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "Sources/Server.swift": (
                "import Glibc\nsetsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &on, 4)\n"
            )
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["swift-http-api"], "SO_REUSEADDR marks a socket server, not a CLI"


def test_a_swift_package_still_resolves_to_the_swift_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {"Package.swift": "// swift-tools-version:5.9\n", "Sources/main.swift": "print(1)\n"},
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["swift-cli"], "the swift service must not claim a plain package"


def test_an_sml_socket_server_resolves_to_the_sml_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "app.mlb": "$(SML_LIB)/basis/basis.mlb\n",
            "src/server.sml": (
                "val listener : Socket.passive INetSock.stream_sock = "
                "INetSock.TCP.socket ()\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["sml-http-api"], "INetSock marks a socket server, not a CLI"


def test_an_fsharp_socket_server_resolves_to_the_fsharp_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "App.fsproj": '<Project Sdk="Microsoft.NET.Sdk"></Project>\n',
            "src/Server.fs": "let listener = new TcpListener(IPAddress.Parse host, port)\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["fsharp-http-api"], "TcpListener marks a socket server, not a CLI"


def test_a_plain_fsharp_project_still_resolves_to_the_fsharp_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "App.fsproj": '<Project Sdk="Microsoft.NET.Sdk"></Project>\n',
            "Program.fs": 'printfn "hi"\n',
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["fsharp-cli"], "the fsharp service must not claim a plain project"


def test_a_plain_sml_program_still_resolves_to_the_sml_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {"app.mlb": "$(SML_LIB)/basis/basis.mlb\n", "src/main.sml": 'val () = print "hi\\n"\n'},
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["sml-cli"], "the sml service must not claim a plain program"


def test_a_fortran_socket_server_resolves_to_the_fortran_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "Makefile": "all:\n\tgfortran -o app src/main.f90\n",
            "src/server.f90": (
                'interface\n'
                '  function c_socket(domain, kind, protocol) bind(c, name="socket")\n'
                'end interface\n'
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["fortran-http-api"], "a bind(c) socket call marks a service, not a CLI"


def test_a_plain_fortran_program_still_resolves_to_the_fortran_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "Makefile": "all:\n\tgfortran -o app src/main.f90\n",
            "src/main.f90": "program main\nend program main\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["fortran-cli"], "the fortran service must not claim a plain program"


def test_an_octave_socket_server_resolves_to_the_octave_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "main.m": "addpath('lib');\nserve('127.0.0.1', 8080);\n",
            "lib/serve.m": (
                "function serve(host, port)\n"
                "  s = javaObject('java.net.ServerSocket');\n"
                "end\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["octave-http-api"], "the JVM server socket marks a service, not a CLI"


def test_a_plain_octave_script_still_resolves_to_the_octave_cli(tmp_path) -> None:
    make_repo(tmp_path, {"main.m": "printf('hi\\n');\n"})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["octave-cli"], "the octave service must not claim a plain script"


def test_a_kotlin_jdk_server_resolves_to_the_kotlin_service(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "pom.xml": "<project><artifactId>svc</artifactId></project>\n",
            "src/main/kotlin/Server.kt": (
                "import com.sun.net.httpserver.HttpServer\n"
                "\n"
                "fun serve() = HttpServer.create()\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["kotlin-http-api"], "the JDK server marks a service, not a CLI"


def test_a_plain_kotlin_project_still_resolves_to_the_kotlin_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "pom.xml": (
                "<project><artifactId>cli</artifactId>"
                "<dependency>kotlin-stdlib</dependency></project>\n"
            ),
            "src/main/kotlin/Main.kt": "fun main() = println(\"hi\")\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["kotlin-cli"], "the kotlin service must not claim a plain project"

def test_a_fastapi_service_with_wal_sqlite_resolves_to_the_sqlite_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "pyproject.toml": (
                "[project]\n"
                'name = "notes"\n'
                'dependencies = ["fastapi>=0.115", "uvicorn[standard]>=0.30"]\n'
            ),
            "src/notes/db.py": (
                "import sqlite3\n"
                "\n"
                "\n"
                "def connect(path):\n"
                "    connection = sqlite3.connect(path)\n"
                '    connection.execute("PRAGMA journal_mode=WAL")\n'
                "    return connection\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["python-fastapi-sqlite"], "WAL is the marker of the stateful service"


def test_a_plain_fastapi_project_still_resolves_to_the_fastapi_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "pyproject.toml": (
                "[project]\n"
                'name = "api"\n'
                'dependencies = ["fastapi>=0.115"]\n'
            ),
            "src/api/main.py": (
                "from fastapi import FastAPI\n"
                "\n"
                "app = FastAPI()\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["fastapi"], "a service without SQLite must not adopt the schema stack"

def test_a_websocket_server_resolves_to_the_node_ws_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "package.json": '{"name": "chat", "type": "module", "dependencies": {"ws": "^8"}}\n',
            "src/server.js": (
                'import { WebSocketServer } from "ws";\n'
                "\n"
                "export const sockets = new WebSocketServer({ noServer: true });\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["node-ws-api"], "an upgrade server is not an HTTP-only API"


def test_a_plain_javascript_project_does_not_match_the_ws_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "package.json": '{"name": "tool", "type": "module", "dependencies": {"ws": "^8"}}\n',
            "src/client.js": (
                'import { WebSocket } from "ws";\n'
                "\n"
                "export const socket = new WebSocket(process.env.URL);\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == [], "a client that consumes ws must not claim the server stack"

def test_a_go_worker_resolves_to_the_worker_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "go.mod": "module example.com/jobs\n\ngo 1.24\n",
            "main.go": (
                "package main\n"
                "\n"
                'import "flag"\n'
                "\n"
                "func main() {\n"
                '\t// -state is the path to the idempotency ledger\n'
                '\tflag.String("state", "seen.json", "")\n'
                "\tflag.Parse()\n"
                "}\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    # go.mod alone matches the CLI and the HTTP service by design; the worker's
    # content marker still wins outright because it is the only content-aware match.
    assert names == ["go-worker"], "a ledger-driven batch worker is not a plain Go CLI"


def test_a_plain_go_program_still_resolves_to_the_go_cli(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "go.mod": "module example.com/hello\n\ngo 1.24\n",
            "main.go": "package main\n\nfunc main() { println(\"hi\") }\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    # Still the CLI/service pair: the worker must not claim every Go module.
    assert names == ["go-cli", "go-http"], "the worker must not claim every Go project"


def test_a_server_sent_events_server_resolves_to_the_sse_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "pyproject.toml": (
                "[project]\n"
                'name = "events"\n'
                'dependencies = ["fastapi", "uvicorn"]\n'
            ),
            "src/events/routes.py": (
                "from fastapi.responses import StreamingResponse\n"
                "\n"
                'MEDIA = "text/event-stream"\n'
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["python-sse-api"], "a stream is not a plain FastAPI app"


def test_a_plain_fastapi_app_does_not_match_the_sse_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "pyproject.toml": (
                "[project]\n"
                'name = "api"\n'
                'dependencies = ["fastapi"]\n'
            ),
            "app.py": "from fastapi import FastAPI\n\napp = FastAPI()\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert "python-sse-api" not in names, "the sse stack must not claim every FastAPI app"


def test_a_go_token_service_resolves_to_the_jwt_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "go.mod": "module x\n\ngo 1.24\n",
            "password.go": (
                "package main\n\n"
                'return fmt.Sprintf("pbkdf2-sha256$%d$%s$%s", rounds, salt, key), nil\n'
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["go-jwt-api"], "a token service must not come out ambiguous against go.mod"


def test_a_go_worker_does_not_match_the_jwt_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "go.mod": "module x\n\ngo 1.24\n",
            "main.go": "package main\n\nimport \"fmt\"\n\nfunc main() { fmt.Println(\"hi\") }\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert "go-jwt-api" not in names, "a plain Go module is not a token service"

def test_a_resumable_upload_service_resolves_to_the_upload_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "package.json": '{"name": "uploads", "type": "module"}\n',
            "src/routes.js": (
                "export function route(store) {\n"
                '  throw new Error("offset_mismatch");\n'
                "}\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["node-upload-api"], "an offset-checking upload service is its own stack"


def test_a_plain_node_project_does_not_match_the_upload_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "package.json": '{"name": "plain", "type": "module"}\n',
            "src/index.js": 'import { createServer } from "node:http";\n',
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert "node-upload-api" not in names, "a bare node server is not an upload service"

def test_a_claiming_scheduler_resolves_to_the_scheduler_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "pyproject.toml": '[project]\nname = "sched"\n',
            "src/sched/jobs.py": (
                'def claim(connection, at):\n'
                '    connection.execute("BEGIN IMMEDIATE")\n'
                "    return []\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["python-scheduler-api"], (
        "an immediate-transaction claim is the scheduler marker"
    )


def test_a_plain_fastapi_app_does_not_match_the_scheduler_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "pyproject.toml": '[project]\nname = "app"\n',
            "app.py": "from fastapi import FastAPI\n\napp = FastAPI()\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert "python-scheduler-api" not in names, "a plain FastAPI app is not a scheduler"

@pytest.mark.parametrize("stack", STACK_LIST, ids=[stack.name for stack in STACK_LIST])
def test_every_stack_can_adopt_into_a_project_it_detects(stack, tmp_path):
    """`adopt` must be able to act on every stack, not just the ones with tests.

    The plan is built from the same synthetic marker directory the detection test
    uses, so a stack that declares adoptable files but renders them with an
    unknown placeholder (or asks for a file adopt refuses to write) fails here
    instead of failing in a user's repository.
    """
    for rule in stack.detect:
        target = tmp_path / _path_for(rule.file)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rule.contains or "marker\n", encoding="utf-8")

    context = build_context_for_check(stack, "demo")
    plan = plan_adoption(stack, tmp_path, context, with_tests=bool(stack.adopt_tests))

    assert plan.added, f"{stack.name} would add nothing to a project it detects"
    assert not (set(plan.added) & FORBIDDEN), (
        f"{stack.name} would overwrite project identity: {sorted(set(plan.added) & FORBIDDEN)}"
    )
    if stack.adopt_tests:
        assert plan.tests_available, f"{stack.name} promises adopt_tests but plans none"


def test_a_fastify_service_resolves_to_the_fastify_stack(tmp_path) -> None:
    make_repo(tmp_path, {"package.json": '{"dependencies": {"fastify": "^5.12.8"}}'})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["fastify-api"]


def test_an_express_project_does_not_match_the_fastify_stack(tmp_path) -> None:
    make_repo(tmp_path, {"package.json": '{"dependencies": {"express": "^5"}}'})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert "fastify-api" not in names


def test_an_angular_workspace_resolves_to_the_angular_app(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "package.json": '{"dependencies": {"@angular/core": "^22.2.0"}}',
            "angular.json": '{"version": 1, "projects": {"demo": {}}}',
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["angular-app"]


def test_a_react_project_does_not_match_the_angular_app(tmp_path) -> None:
    make_repo(tmp_path, {"package.json": '{"dependencies": {"react": "^19"}}'})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert "angular-app" not in names


def test_a_playwright_suite_resolves_to_the_e2e_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "package.json": '{"devDependencies": {"@playwright/test": "^1.64.1"}}',
            "playwright.config.ts": "export default {};\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["playwright-e2e"]


def test_a_plain_node_project_does_not_match_the_e2e_stack(tmp_path) -> None:
    make_repo(tmp_path, {"package.json": '{"name": "demo"}'})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert "playwright-e2e" not in names


def test_an_actix_service_resolves_to_the_actix_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "Cargo.toml": '[package]\nname = "svc"\n\n[dependencies]\nactix-web = "4"\n',
            "src/main.rs": "fn main() {}\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["actix-web"]


def test_a_plain_cargo_project_does_not_match_the_actix_stack(tmp_path) -> None:
    make_repo(tmp_path, {"Cargo.toml": '[package]\nname = "demo"\n'})
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert "actix-web" not in names


def test_a_sqlx_service_resolves_to_the_sqlx_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "Cargo.toml": (
                '[package]\nname = "svc"\n\n'
                '[dependencies]\naxum = "0.8"\nsqlx = { version = "0.8", features = ["sqlite"] }\n'
            ),
            "src/main.rs": "fn main() {}\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["rust-sqlx-api"]


def test_a_plain_axum_project_does_not_match_the_sqlx_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {"Cargo.toml": '[package]\nname = "demo"\n\n[dependencies]\naxum = "0.8"\n'},
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert "rust-sqlx-api" not in names


def test_a_signed_webhook_receiver_resolves_to_the_webhook_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "pyproject.toml": (
                '[project]\nname = "hooks"\ndependencies = ["fastapi>=0.115", "uvicorn>=0.30"]\n'
            ),
            "src/hooks/signature.py": (
                "import hmac\n\n\ndef good(expected, header):\n"
                "    return hmac.compare_digest(expected, header)\n"
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["python-webhook-receiver"]


def test_a_plain_fastapi_app_does_not_match_the_webhook_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "pyproject.toml": '[project]\nname = "api"\ndependencies = ["fastapi"]\n',
            "app.py": "from fastapi import FastAPI\n\napp = FastAPI()\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert "python-webhook-receiver" not in names


def test_a_bun_sqlite_service_resolves_to_the_bun_sqlite_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "package.json": '{"name": "notes", "type": "module"}\n',
            "src/db.js": (
                'import { Database } from "bun:sqlite";\n'
                'export const open = () => new Database("x.db");\n'
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["bun-sqlite-api"]


def test_a_plain_bun_service_does_not_match_the_bun_sqlite_stack(tmp_path) -> None:
    make_repo(
        tmp_path,
        {
            "package.json": '{"name": "api", "type": "module"}\n',
            "src/server.js": "export default { fetch: () => new Response('ok') };\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert "bun-sqlite-api" not in names

def test_a_metrics_exporter_resolves_to_the_metrics_stack(tmp_path):
    write_tree(
        tmp_path,
        {
            "package.json": '{"name": "metrics", "type": "module"}\n',
            "src/app.js": (
                'const headers = { "content-type": "text/plain; version=0.0.4; charset=utf-8" };\n'
            ),
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert names == ["node-metrics-exporter"]


def test_a_plain_node_service_does_not_match_the_metrics_stack(tmp_path):
    write_tree(
        tmp_path,
        {
            "package.json": '{"name": "plain", "type": "module"}\n',
            "src/server.js": "export default { fetch: () => new Response('ok') };\n",
        },
    )
    names = [stack.name for stack in detect_stacks(tmp_path)]
    assert "node-metrics-exporter" not in names
