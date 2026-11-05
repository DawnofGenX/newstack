"""End-to-end checks on the shipped stacks.

The structural tests always run. The expensive ones (installing and building each
generated project) run when NEWSTACK_RUN_VERIFY=1, which is what CI sets.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from newstack.registry import get_stack, load_stacks, search_roots
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
            if ref.startswith("./"):
                # A repository exercising its own action uses `uses: ./`, which
                # resolves to this checkout — there is no version to pin.
                continue
            assert ACTION_REF_RE.match(ref), f"{workflow.name}: unpinned or odd action ref {ref!r}"


@pytest.mark.parametrize("name", STACK_NAMES)
def test_workflow_files_are_valid_yaml(tmp_path, name: str) -> None:
    """A shipped workflow that is not valid YAML runs zero jobs, silently.

    `run: ./run.sh | grep -q "PASS: done"` is the trap: an unquoted plain scalar cannot
    contain `: `, so the file stops parsing and GitHub reports a run with no jobs at all.
    """
    from newstack.cli import build_context_for_check
    from newstack.registry import get_stack
    from newstack.render import generate

    yaml = pytest.importorskip("yaml")

    stack = get_stack(name)
    context = build_context_for_check(stack, "sample-app")
    generate(stack.template_dir, tmp_path, context)

    workflows = list(tmp_path.glob(".github/workflows/*.yml")) + list(
        tmp_path.glob(".github/workflows/*.yaml")
    )
    assert workflows, f"{name} ships no CI workflow"
    for workflow in workflows:
        try:
            parsed = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        except yaml.YAMLError as error:
            pytest.fail(f"{workflow.name}: not valid YAML\n{error}")
        assert isinstance(parsed, dict), workflow
        assert parsed.get("jobs"), f"{workflow.name}: no jobs"


# Every `run:` step executes as `bash -e {0}`, so `cmd; test $? -eq 2` kills the step on
# `cmd` itself — the assertion never runs and the job fails exactly when the CLI is right.
# Capture the status first (`set +e ... status=$? ... test "$status" -eq 2`).
SET_E_ASSERTION_RE = re.compile(r";\s*test\s+\"?\$\?\"?\s+-eq")


@pytest.mark.parametrize("name", STACK_NAMES)
def test_workflow_exit_code_assertions_survive_bash_e(tmp_path, name: str) -> None:
    from newstack.cli import build_context_for_check
    from newstack.registry import get_stack
    from newstack.render import generate

    stack = get_stack(name)
    context = build_context_for_check(stack, "sample-app")
    generate(stack.template_dir, tmp_path, context)

    for workflow in tmp_path.glob(".github/workflows/*.y*ml"):
        for lineno, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
            assert not SET_E_ASSERTION_RE.search(line), (
                f"{name}/{workflow.name}:{lineno}: `$?` is tested after `;` — under "
                f"`bash -e` the step dies before the test runs: {line.strip()!r}"
            )


# `dotnet test --no-build` reuses the last build's configuration, and the default is Debug.
# A workflow that builds Release and then tests with `--no-build` alone asks for a Debug test
# assembly that was never produced: "The argument .../tests/bin/Debug/net8.0/*.Tests.dll is
# invalid", step exit 1 — while `newstack check` (plain `dotnet test`) stays green.
DOTNET_NO_BUILD_RE = re.compile(r"dotnet test[^\n]*--no-build")
DOTNET_BUILD_CONFIG_RE = re.compile(r"dotnet build[^\n]*?-c\s+(?P<config>[A-Za-z]+)")


@pytest.mark.parametrize("name", STACK_NAMES)
def test_dotnet_no_build_steps_name_the_configuration_they_reuse(tmp_path, name: str) -> None:
    from newstack.cli import build_context_for_check
    from newstack.registry import get_stack
    from newstack.render import generate

    stack = get_stack(name)
    context = build_context_for_check(stack, "sample-app")
    generate(stack.template_dir, tmp_path, context)

    for workflow in tmp_path.glob(".github/workflows/*.y*ml"):
        text = workflow.read_text(encoding="utf-8")
        configs = [m.group("config") for m in DOTNET_BUILD_CONFIG_RE.finditer(text)]
        if not configs or configs[-1].lower() == "debug":
            continue  # nothing was built in a configuration other than the default
        config = configs[-1]
        for lineno, line in enumerate(text.splitlines(), 1):
            if not DOTNET_NO_BUILD_RE.search(line):
                continue
            assert f"-c {config}" in line, (
                f"{name}/{workflow.name}:{lineno}: the workflow builds {config} but this "
                f"step tests with `--no-build` and no `-c {config}`, so it looks for the "
                f"Debug assembly: {line.strip()!r}"
            )


# Actions that ship exact tags but no moving major tag: `@v1` resolves to nothing and the
# job dies before its first step. Verified against `git ls-remote --tags` for each repo.
ACTIONS_WITHOUT_MOVING_MAJOR = ("astral-sh/setup-uv", "crystal-lang/install-crystal")


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
            action = ref.split("@", 1)[0]
            if action in ACTIONS_WITHOUT_MOVING_MAJOR:
                tag = ref.split("@", 1)[1]
                assert re.fullmatch(r"v\d+\.\d+\.\d+", tag), (
                    f"{workflow.name}: {action} publishes no moving major tag, pin the "
                    f"patch version (got {tag!r})"
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
def test_node_workflow_never_needs_a_missing_lockfile(tmp_path, name: str) -> None:
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
        needs_lockfile = [line for line in lines if "npm ci" in line or "cache: npm" in line]
        if needs_lockfile:
            assert (tmp_path / "package-lock.json").is_file(), (
                f"{name}/{workflow.name} uses {needs_lockfile[0].strip()!r} but the template "
                "ships no package-lock.json, so the generated project's first CI run fails "
                "in actions/setup-node before any install happens"
            )


@pytest.mark.parametrize("name", STACK_NAMES)
def test_every_http_step_only_trusts_the_listener_it_started(name: str) -> None:
    """A step that curls a port must prove it is talking to its own server.

    Without the pre-flight probe a stale process on the same port answers every
    request and the step passes while the stack is broken; without ``kill -0`` a
    server that died on boot is indistinguishable from one that is slow; without
    ``--max-time`` a half-open connection waits until the step times out.
    """
    stack = get_stack(name)
    for step in stack.verify:
        cmd = step.cmd
        if "curl" not in cmd:
            continue
        assert "already" in cmd, f"{name}: step {step.name!r} never checks the port is free"
        assert "kill -0" in cmd, f"{name}: step {step.name!r} never checks its server is alive"
        assert "--max-time" in cmd, f"{name}: step {step.name!r} can hang on a stalled server"


@pytest.mark.parametrize("name", STACK_NAMES)
def test_every_multiline_http_step_fails_loudly(name: str) -> None:
    """A multi-line step must not end with ``|| true`` and call it a pass.

    ``newstack check`` runs each step through ``sh -c``, which does not stop at
    the first failing command. A step written as a list of bare assertions and
    finished with ``wait $server || true`` therefore reports success even when
    every assertion failed. ``set -e`` makes the assertions fatal; the EXIT trap
    then stops the server on the failure path, where the closing ``kill`` never
    runs.
    """
    stack = get_stack(name)
    for step in stack.verify:
        cmd = step.cmd
        if "curl" not in cmd or "\n" not in cmd:
            continue
        last = [line for line in cmd.splitlines() if line.strip()][-1].strip()
        if cmd.startswith("set -e\n"):
            assert "trap '" in cmd and "EXIT" in cmd, (
                f"{name}: step {step.name!r} uses `set -e` and must also trap EXIT "
                "to stop its server on the failure path"
            )
            continue
        assert not last.endswith("|| true"), (
            f"{name}: step {step.name!r} ends with `|| true`, so every assertion in it "
            "can fail and the step still reports success"
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
    from newstack.cli import build_context_for_check
    from newstack.registry import get_stack
    from newstack.render import render_string

    stack = get_stack(name)
    pyproject = stack.template_dir / "pyproject.toml"
    workflow = stack.template_dir / ".github" / "workflows" / "ci.yml"
    if not pyproject.is_file() or not workflow.is_file():
        pytest.skip("not a Python stack")

    # compare what the stack actually generates, so a --python placeholder counts
    context = build_context_for_check(stack, "check-app")
    spec = re.search(
        r'requires-python\s*=\s*"([^"]+)"',
        render_string(pyproject.read_text(encoding="utf-8"), context),
    )
    matrix = re.search(
        r"python-version:\s*\[([^\]]+)\]",
        render_string(workflow.read_text(encoding="utf-8"), context),
    )
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


COUNTER_STACKS = (
    "react-vite-ts",
    "vue-vite-ts",
    "svelte-kit-ts",
    "next-app-ts",
    "chrome-extension",
)


def test_every_counter_demo_persists_under_one_key() -> None:
    """One idea, five stacks: the demo counter survives a reload the same way everywhere.

    The key is the contract. If a stack drifts to its own storage key, a reader who learns
    the pattern in one starter is misled in the next.
    """
    stacks = load_stacks()
    suffixes = {".ts", ".tsx", ".svelte", ".vue"}
    for name in COUNTER_STACKS:
        root = stacks[name].template_dir
        hits = [
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.suffix in suffixes
            and "newstack:counter" in path.read_text(encoding="utf-8", errors="ignore")
        ]
        assert hits, f"{name} ships a counter that does not persist under the shared key"


def test_every_template_file_is_tracked_by_git() -> None:
    """A template's own .gitignore also applies to the template tree in THIS repo.

    An unanchored rule such as `{{ package_name }}` therefore hides a template
    directory from git, and the CI checkout - the install path that actually
    matters - is missing files that exist on the maintainer's disk. That is how
    nim-cli first shipped without src/<package>/counting.nim.
    """
    root = Path(__file__).resolve().parents[1]
    if not (root / ".git").exists():
        pytest.skip("not a git checkout")
    listed = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, text=True, check=False
    )
    if listed.returncode != 0:
        pytest.skip("git ls-files is unavailable")
    tracked = {item for item in listed.stdout.split("\0") if item}
    missing = []
    for stack in load_stacks().values():
        for path in sorted(stack.template_dir.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if relative not in tracked:
                missing.append(relative)
    assert not missing, (
        "template files ignored by git, so CI checkouts lack them "
        f"(anchor the offending .gitignore rule): {missing}"
    )

@pytest.mark.parametrize("name", STACK_NAMES)
def test_every_uv_install_step_is_idempotent(name: str) -> None:
    """`uv venv` refuses a directory it already made.

    A developer who runs the documented steps twice — or a second `check` against
    a render someone kept around — must not be told their environment already
    exists. `--allow-existing` makes the step repeatable instead of version
    dependent.
    """
    stack = get_stack(name)
    for step in stack.verify:
        if "uv venv" in step.cmd:
            assert "--allow-existing" in step.cmd, (
                f"{name}: the {step.name} step creates a venv without --allow-existing, "
                "so running it twice fails"
            )

FOUR_XX = re.compile(r"\b(404|405|409|413|422)\b")


@pytest.mark.parametrize("name", STACK_NAMES)
def test_no_template_curl_fails_on_an_expected_error_status(name):
    """`curl -f` swallows the very 4xx a check is asserting.

    Two stacks shipped this: a `curl -fsS … -d '{}'` line expecting a 422 produced
    `curl: (22) The requested URL returned error: 422` and an empty body, so the step
    failed on the runner while `newstack check` passed locally (bash does not run the
    ship-time step). Any line that names a 4xx must use plain `-sS`.
    """
    stack = get_stack(name)
    offenders = []
    for path in sorted(stack.template_dir.rglob("*")):
        if not path.is_file() or path.suffix not in {".yml", ".yaml", ".sh"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), 1):
            if ("-fsS" in line or "--fail" in line) and FOUR_XX.search(line):
                rel = path.relative_to(stack.template_dir)
                offenders.append(f"{rel}:{lineno}: {line.strip()}")
    message = f"{name}: curl -f on a line that expects a 4xx converts the answer into an error"
    assert not offenders, f"{message}: {offenders}"

SINGLE_BRACE = re.compile(r"(?<![%${])\{([a-z][a-z0-9_]*)\}(?!\})")


@pytest.mark.parametrize("name", STACK_NAMES)
def test_every_verify_command_uses_double_braces(name):
    """A verify command is rendered with `{{ }}`, so a single-brace `{key}` survives.

    `next_steps` are the other way round: `cli.py::_format_step` renders them with
    `str.format_map`, so they need single braces. Mixing the two is silent — the step runs
    with a literal `{package_name}` and the failure reads like a broken project
    (`.venv/bin/python: No module named {package_name}`), not like a bad placeholder.
    Only names from the stack's own render context count: `%{http_code}`, `${var}` and a
    Python f-string like `{events}` inside a heredoc are real syntax, not placeholders.
    """
    from newstack.cli import build_context_for_check

    stack = get_stack(name)
    keys = build_context_for_check(stack, "demo")
    offenders = []
    for step in stack.verify:
        for match in SINGLE_BRACE.finditer(step.cmd):
            if match.group(1) in keys:
                offenders.append(f"{step.name}: {match.group(0)}")
    assert not offenders, (
        f"{name}: verify commands render with {{{{ }}}}; these placeholders stay literal: "
        f"{offenders}"
    )


# scripts/proof_stack.sh scaffolds into `newstack-smoke-<stack>-<epoch>`, so the
# rendered package name is 44 characters. A line that fits at `demo` can therefore
# break in the one place a stack's CI actually runs.
PROOF_PROJECT_NAME = "newstack-smoke-python-duckdb-report-1793898647"
DEFAULT_COLUMNS = 100


def _configured_columns(project: Path) -> int | None:
    """The line length ruff would enforce in the rendered project, if it enforces one.

    ruff's default rule set stops at E4/E7/E9, which excludes E501 - a stack that
    lists `E` (or `E501`) in `select` is the only kind that can fail on a long line.
    Parsed as text because the CLI itself still runs on Python 3.10, where `tomllib`
    does not exist.
    """
    manifest = project / "pyproject.toml"
    if not manifest.is_file():
        return None
    text = manifest.read_text(encoding="utf-8")
    selected = " ".join(
        match.group(1) for match in re.finditer(r"(?:extend-)?select\s*=\s*\[([^\]]*)\]", text)
    )
    if not re.search(r'"(?:E|E5[0-9]{2})"', selected):
        return None
    columns = re.search(r"^line[-_]length\s*=\s*([0-9]+)", text, re.MULTILINE)
    return int(columns.group(1)) if columns else DEFAULT_COLUMNS


@pytest.mark.parametrize("name", STACK_NAMES)
def test_a_long_project_name_still_fits_the_line_length(tmp_path, name: str) -> None:
    """A proof run renders a 44-character project name, so templates are linted at that size.

    `from {{ package_name }}.module import a, b, c` grows with the package name: at
    `demo` it fits, at a proof-run name it is 117 columns, and the hosted run then dies
    in Lint before a single test executes.
    """
    from newstack.cli import build_context_for_check
    from newstack.render import generate

    stack = get_stack(name)
    context = build_context_for_check(stack, PROOF_PROJECT_NAME)
    generate(stack.template_dir, tmp_path, context)
    columns = _configured_columns(tmp_path)
    if columns is None:
        pytest.skip("this stack does not lint for long lines")
    offenders = []
    for path in sorted(tmp_path.rglob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if len(line) > columns:
                offenders.append(f"{path.relative_to(tmp_path).as_posix()}:{number} ({len(line)})")
    assert not offenders, (
        f"{name}: lines wider than {columns} columns once the project name is "
        f"{len(PROOF_PROJECT_NAME)} characters: {offenders}"
    )


def _uploaded_file_targets(text: str) -> list[str]:
    """Every single-file path an upload-artifact step names (directories are skipped)."""
    targets: list[str] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("path:"):
            continue
        value = stripped[len("path:"):].strip()
        if value in {"|", ">", "|-", ">-"}:
            indent = len(line) - len(line.lstrip())
            for follow in lines[index + 1:]:
                if not follow.strip():
                    continue
                if len(follow) - len(follow.lstrip()) <= indent:
                    break
                targets.append(follow.strip())
        elif value:
            targets.append(value)
    return [
        target
        for target in targets
        if not target.endswith("/") and "*" not in target and "." in target.rsplit("/", 1)[-1]
    ]


@pytest.mark.parametrize("name", STACK_NAMES)
def test_every_uploaded_artifact_is_created_by_the_same_workflow(name: str) -> None:
    """An upload that names a file nothing produces fails only on the runner.

    `newstack check` never executes the workflow, so a `path: report.pdf` whose file is
    built and cleaned up inside a temp directory looks fine locally and turns the job red
    with "No files were found with the provided path". Directory uploads (a test report a
    tool writes itself) are out of scope; single files are not.
    """
    stack = get_stack(name)
    workflows = stack.template_dir / ".github" / "workflows"
    if not workflows.is_dir():
        pytest.skip(f"{name} ships no workflow")
    for workflow in sorted(workflows.glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        if "actions/upload-artifact" not in text:
            continue
        for target in _uploaded_file_targets(text):
            creators = [
                line
                for line in text.splitlines()
                if target in line and not line.strip().startswith("path:")
            ]
            assert creators, (
                f"{name}/{workflow.name} uploads {target!r} but nothing in that workflow "
                "creates it"
            )

STDLIB_IMPORTS = frozenset(
    {
        "__future__",
        "collections",
        "csv",
        "dataclasses",
        "datetime",
        "json",
        "logging",
        "os",
        "pathlib",
        "re",
        "shutil",
        "sqlite3",
        "subprocess",
        "sys",
        "tempfile",
        "time",
        "typing",
        "urllib",
    }
)
IMPORT_LINE = re.compile(r"(?m)^\s*(?:import|from)\s+([A-Za-z_][A-Za-z0-9_]*)")


@pytest.mark.parametrize("name", STACK_NAMES)
def test_python_workflows_import_the_rendered_package(name: str) -> None:
    """A workflow that imports the sample module only works for the sample.

    ``newstack check`` never runs the workflow, so a hardcoded ``import
    textstat`` in a CI step stays invisible until the runner renders a project
    with a different name and dies with ModuleNotFoundError.
    """
    stack = get_stack(name)
    if stack.language != "python":
        pytest.skip("not a python stack")
    workflow = stack.directory / "template/.github/workflows/ci.yml"
    if not workflow.exists():
        return
    text = workflow.read_text(encoding="utf-8")
    imported = {match.group(1) for match in IMPORT_LINE.finditer(text)}
    offenders = sorted(imported - STDLIB_IMPORTS)
    assert not offenders, (
        f"{name} imports {offenders} in its workflow; "
        "use {{ package_name }} so the rendered project works"
    )


PIPE_HEAD = re.compile(r"\|\s*head\b")


def _pipefail_offences(text: str) -> list[int]:
    """Line numbers where a `| head` truncation can trip `set -o pipefail`.

    A head that exits after its share leaves the producer writing into a closed
    pipe; the producer then dies with SIGPIPE and, under `pipefail`, the whole
    pipeline reports 141. In a smoke script that aborts the step about one run
    in three, which looks exactly like an intermittent product bug.
    """
    lines = text.splitlines()
    if not any("pipefail" in line for line in lines):
        return []
    offences: list[int] = []
    for index, line in enumerate(lines):
        # A comment that names the pattern is documentation, not a pipeline.
        if line.lstrip().startswith("#"):
            continue
        if PIPE_HEAD.search(line) is None:
            continue
        window = " ".join(lines[index : index + 3])
        if "|| true" in line or "PIPESTATUS" in window or "pipefail-ok" in line:
            continue
        offences.append(index + 1)
    return offences


@pytest.mark.parametrize("name", STACK_NAMES)
def test_no_template_head_can_trip_pipefail(name: str) -> None:
    """A template shell script must not die of its own diagnostics.

    The stacks run with `set -euo pipefail`; every deliberate truncation has to
    say so with `|| true` (or assert PIPESTATUS, like node-cli's EPIPE test).
    """
    template = get_stack(name).template_dir
    offenders: list[str] = []
    for path in sorted(template.rglob("*.sh")):
        for line in _pipefail_offences(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.relative_to(template)}:{line}")
    assert not offenders, f"{name}: | head can trip pipefail: {offenders}"
