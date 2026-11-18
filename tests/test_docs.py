"""Docs drift guards: the README and CI must not fall behind the registry."""

from __future__ import annotations

import re
from pathlib import Path

from newstack.registry import load_stacks

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
CI = ROOT / ".github" / "workflows" / "ci.yml"
STACKS_ROOT = ROOT / "src" / "newstack" / "data" / "stacks"


def test_readme_exists() -> None:
    assert README.is_file()


def test_every_stack_is_in_the_readme_table() -> None:
    text = README.read_text(encoding="utf-8")
    missing = [name for name in load_stacks() if f"| `{name}` |" not in text]
    assert not missing, f"README stack table is missing: {', '.join(missing)}"


def test_every_stack_is_in_the_ci_matrix() -> None:
    text = CI.read_text(encoding="utf-8")
    missing = []
    for name in load_stacks():
        pattern = rf"^\s*-\s*{re.escape(name)}\s*$"
        if not re.search(pattern, text, re.M):
            missing.append(name)
    assert not missing, f"ci.yml stack matrix is missing: {', '.join(missing)}"


def _readme_rows() -> list[str]:
    """Stack names in the README table, one per row, in file order."""
    text = README.read_text(encoding="utf-8")
    return re.findall(r"^\|\s*`([a-z0-9][a-z0-9-]*)`\s*\|", text, re.M)


def test_readme_lists_each_stack_exactly_once() -> None:
    """A duplicated row is drift too: it makes the table count lie about the registry."""
    rows = _readme_rows()
    duplicated = sorted({name for name in rows if rows.count(name) > 1})
    assert not duplicated, f"README stack table lists twice: {', '.join(duplicated)}"
    assert sorted(rows) == sorted(load_stacks()), (
        f"README has {len(rows)} rows for {len(load_stacks())} stacks"
    )


def _ci_matrix_blocks() -> dict[str, list[str]]:
    """Map each stack-sharding job in ci.yml to the names in its matrix, in file order.

    The stack job is split across several matrices (see docs/CI.md): a single
    matrix stops expanding once it reaches 256 entries, and a matrix that does
    not expand makes the run fail with no per-stack jobs at all.
    """
    lines = CI.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line == "jobs:")
    except StopIteration:  # pragma: no cover - a workflow without jobs is not a workflow
        raise AssertionError("ci.yml has no top-level `jobs:` section") from None
    blocks: dict[str, list[str]] = {}
    job: str | None = None
    in_matrix = False
    for line in lines[start + 1 :]:
        header = re.match(r"^ {2}([A-Za-z0-9_-]+):\s*$", line)
        if header:
            job, in_matrix = header.group(1), False
            continue
        if line.strip() == "stack:" and job is not None:
            in_matrix = True
            blocks.setdefault(job, [])
            continue
        if in_matrix and job is not None:
            if line.startswith("          - "):
                blocks[job].append(line.strip()[2:].strip())
            elif line.strip():
                in_matrix = False
    return blocks


def _ci_matrix_entries() -> list[str]:
    """Every stack named by any shard matrix, in file order."""
    return [name for entries in _ci_matrix_blocks().values() for name in entries]


def test_ci_matrix_lists_each_stack_exactly_once() -> None:
    """A duplicate matrix entry runs the same stack twice and hides a missing one."""
    entries = _ci_matrix_entries()
    duplicated = sorted({name for name in entries if entries.count(name) > 1})
    assert not duplicated, f"ci.yml stack matrices list twice: {', '.join(duplicated)}"
    assert sorted(entries) == sorted(load_stacks()), (
        f"ci.yml matrices name {len(entries)} stacks for {len(load_stacks())} in the registry"
    )


def test_every_shard_matrix_stays_under_the_github_limit() -> None:
    """Past 256 entries GitHub silently drops the matrix, so the run proves nothing.

    That is not a slowdown: the job does not expand at all, no `stack X` job is
    created, and the run just reports a failure. Keep every shard well under.
    """
    blocks = _ci_matrix_blocks()
    assert blocks, "ci.yml has no `stack:` matrix to check"
    too_big = {job: len(entries) for job, entries in blocks.items() if len(entries) > 256}
    assert not too_big, f"matrix over the 256-job expansion cap (it will not expand): {too_big}"


def test_shard_matrices_are_balanced() -> None:
    """One empty or one giant shard means the split stopped doing its job."""
    sizes = [len(entries) for entries in _ci_matrix_blocks().values() if entries]
    assert sizes, "ci.yml has no non-empty stack matrix"
    assert min(sizes) > 0
    assert max(sizes) <= 2 * min(sizes), f"shard sizes are lopsided: {sorted(sizes)}"


def test_stack_shards_share_one_step_list() -> None:
    """Four copies of the 60-odd toolchain gates drift apart on the first edit."""
    text = CI.read_text(encoding="utf-8")
    blocks = _ci_matrix_blocks()
    assert len(blocks) > 1, "expected the stack job to be sharded"
    assert text.count("    steps: &shared_setup") == 1, (
        "ci.yml must define the shared step list exactly once, as `    steps: &shared_setup`"
    )
    used = text.count("    steps: *shared_setup")
    assert used == len(blocks) - 1, (
        f"{len(blocks)} stack jobs but {used + 1} use the shared step list"
    )
    # A top-level anchor key is dropped by the workflow schema, which breaks the
    # aliases; anchoring on the first shard is the form GitHub actually expands.
    anchor = text.split("    steps: &shared_setup", 1)[1].split("\n  stacks-", 1)[0]
    assert "fromJSON(" in anchor, "the toolchain gates must live in the shared step list"
    assert anchor.count("      - name:") + anchor.count("  - name:") >= 20, (
        "the shared step list looks truncated"
    )


def test_readme_states_no_stack_count_that_can_go_stale() -> None:
    """A hardcoded count is drift bait once a stack is added; the table is the source."""
    text = README.read_text(encoding="utf-8")
    assert not re.search(r"\b(\d+|six|seven|eight|nine|ten)\s+(stacks|starters)\b", text, re.I)


def _ci_job_blocks() -> dict[str, list[str]]:
    """Map each job name in ci.yml to the lines that belong to it."""
    lines = CI.read_text(encoding="utf-8").splitlines()
    try:
        start = next(i for i, line in enumerate(lines) if line == "jobs:")
    except StopIteration:  # pragma: no cover
        raise AssertionError("ci.yml has no top-level `jobs:` section") from None
    blocks: dict[str, list[str]] = {}
    job: str | None = None
    for line in lines[start + 1 :]:
        header = re.match(r"^ {2}([A-Za-z0-9_-]+):\s*$", line)
        if header:
            job = header.group(1)
            blocks[job] = [line]
            continue
        if job is not None:
            blocks[job].append(line)
    return blocks


def test_ci_verifies_the_whole_tree_on_a_schedule() -> None:
    """An upstream toolchain move breaks stacks with no push behind it."""
    text = CI.read_text(encoding="utf-8")
    assert re.search(r"^  schedule:$", text, re.M), "ci.yml has no schedule: trigger"
    assert re.search(r"^\s+- cron: '?\d+ \d+ \* \* \*'?$", text, re.M), (
        "the schedule trigger has no cron line"
    )


def test_the_stack_shards_are_gated_on_a_stack_diff_for_pull_requests() -> None:
    """A docs-only PR must not pay for 314 runner jobs, and a stack PR must."""
    blocks = _ci_job_blocks()
    assert "changed" in blocks, "ci.yml has no `changed` job to gate the shards"
    changed = "\n".join(blocks["changed"])
    assert "src/newstack/data/stacks" in changed, "the gating job does not look at the stacks tree"
    # The gating job must run on every event: a job whose `needs` was skipped is
    # skipped too, which would report a green run with no stack verified at all.
    assert "if: github.event_name == 'pull_request'" not in changed.split("steps:")[0], (
        "the `changed` job is itself skipped on push, which skips every shard"
    )
    event_condition = changed.index("if: github.event_name == 'pull_request'")
    assert event_condition > changed.index("steps:"), (
        "the event condition belongs on steps, not on the job"
    )
    for job in _ci_matrix_blocks():
        block = "\n".join(blocks[job])
        assert "needs: changed" in block, f"{job} does not wait for the `changed` job"
        assert "if: needs.changed.outputs.stacks == 'true'" in block, (
            f"{job} is not skipped for a pull request that touches no stack"
        )


def _java_gated_stacks() -> set[str]:
    """Stack names any `actions/setup-java` step in ci.yml applies to."""
    lines = CI.read_text(encoding="utf-8").splitlines()
    gated: set[str] = set()
    for index, line in enumerate(lines):
        if "uses: actions/setup-java@" not in line:
            continue
        # The `if:` for a step sits directly above its `uses:` line.
        for back in range(index - 1, max(index - 6, -1), -1):
            candidate = lines[back].strip()
            if candidate.startswith("- name:") or candidate.startswith("- uses:"):
                break
            if candidate.startswith("if:"):
                gated.update(re.findall(r"[\"']([a-z0-9][a-z0-9-]*)[\"']", candidate))
                gated.update(
                    re.findall(r"matrix\.stack\s*==\s*[\"']([a-z0-9][a-z0-9-]*)", candidate)
                )
                break
    return gated


def test_every_java_build_stack_gets_a_runner_jdk() -> None:
    """The runner default JDK is older than the release these stacks target.

    java-picocli-cli passed locally on a JDK 21 and failed on the runner with
    "error: release version 21 not supported" because no setup-java step named
    it. A stack that compiles with Maven or Gradle has to appear in a gate; an
    interpreter-only stack (groovy/clojure/scala-cli scripts) just needs a JRE
    and the runner image already ships one.
    """
    gated = _java_gated_stacks()
    assert gated, "ci.yml has no actions/setup-java gate at all"
    builders = {"mvn", "mvnw", "gradle", "gradlew"}
    missing = sorted(
        name
        for name, stack in load_stacks().items()
        if "java" in stack.requires
        and builders & set(stack.requires)
        and name not in gated
    )
    assert not missing, (
        f"these stacks need a JDK but no setup-java step names them: {', '.join(missing)}"
    )


def _elixir_gated_stacks() -> set[str]:
    """Stack names any setup-beam step that pins an Elixir version applies to."""
    lines = CI.read_text(encoding="utf-8").splitlines()
    gated: set[str] = set()
    for index, line in enumerate(lines):
        if "uses: erlef/setup-beam@" not in line:
            continue
        # The `with:` block follows the `uses:` line, so the elixir-version pin
        # (rather than the rebar3/Erlang-only step) decides whether this step
        # installs Elixir at all.
        has_elixir = False
        for ahead in range(index + 1, min(index + 8, len(lines))):
            candidate = lines[ahead].strip()
            if candidate.startswith("- name:") or candidate.startswith("- uses:"):
                break
            if candidate.startswith("elixir-version:"):
                has_elixir = True
        if not has_elixir:
            continue
        for back in range(index - 1, max(index - 6, -1), -1):
            candidate = lines[back].strip()
            if candidate.startswith("- name:") or candidate.startswith("- uses:"):
                break
            if candidate.startswith("if:"):
                gated.update(re.findall(r"[\"']([a-z0-9][a-z0-9-]*)[\"']", candidate))
                gated.update(
                    re.findall(r"matrix\.stack\s*==\s*[\"']([a-z0-9][a-z0-9-]*)[\"']", candidate)
                )
                break
    return gated


def test_every_elixir_stack_gets_a_runner_elixir() -> None:
    """mix is not on the runner image; a stack that shells out to it needs the gate.

    elixir-gen-server was wired into a shard without being added to the
    setup-beam condition, so `newstack check` reported "SKIP missing toolchain:
    mix" and the job failed on a green template.
    """
    gated = _elixir_gated_stacks()
    assert gated, "ci.yml has no setup-beam step that installs Elixir"
    missing = sorted(
        name
        for name, stack in load_stacks().items()
        if "mix" in stack.requires and name not in gated
    )
    assert not missing, (
        f"these stacks need Elixir but no setup-beam step names them: {', '.join(missing)}"
    )


GATED_TOOLCHAINS = (
    ("ruby", "uses: ruby/setup-ruby@"),
    ("php", "uses: shivammathur/setup-php@"),
    ("dotnet", "uses: actions/setup-dotnet@"),
)


def _gated_by(action_marker: str) -> set[str]:
    """Stack names any step that uses `action_marker` applies to."""
    lines = CI.read_text(encoding="utf-8").splitlines()
    gated: set[str] = set()
    for index, line in enumerate(lines):
        if action_marker not in line:
            continue
        for back in range(index - 1, max(index - 6, -1), -1):
            candidate = lines[back].strip()
            if candidate.startswith("- name:") or candidate.startswith("- uses:"):
                break
            if candidate.startswith("if:"):
                gated.update(re.findall(r"[\"']([a-z0-9][a-z0-9-]*)[\"']", candidate))
                gated.update(
                    re.findall(r"matrix\.stack\s*==\s*[\"']([a-z0-9][a-z0-9-]*)[\"']", candidate)
                )
                break
    return gated


_USES = re.compile(r"uses:\s*([A-Za-z0-9._-]+/[A-Za-z0-9._-]+)@")
# Actions that are not toolchains: the runner image already provides them, so a
# stack missing from (or absent from) a gate for one of these is not drift.
_NOT_A_TOOLCHAIN = {
    "actions/checkout",
    "actions/upload-artifact",
    "actions/download-artifact",
    "actions/cache",
    "astral-sh/setup-uv",
    "actions/setup-python",
    "actions/setup-node",
    # Go and Rust come from the runner image and every go/rust stack builds on
    # it today (34 go + 24 rust stacks are green in a run where the legacy gate
    # list skipped them), so their stale lists are not drift.
    "actions/setup-go",
    "dtolnay/rust-toolchain",
}

# Stacks whose toolchain comes from a step that is not the action their own
# template workflow happens to use, with the reason it is fine.
_GATE_EXEMPTIONS = {
    "erlang-cli": "gets Erlang from the apt step; only the rebar3 job needs setup-beam",
}


def _template_workflows() -> dict[str, Path]:
    """Stack name -> its template workflow, for stacks that ship one."""
    found: dict[str, Path] = {}
    for stack_dir in sorted(STACKS_ROOT.iterdir()):
        workflow = stack_dir / "template" / ".github" / "workflows" / "ci.yml"
        if stack_dir.is_dir() and workflow.is_file():
            found[stack_dir.name] = workflow
    return found


def test_every_template_toolchain_is_named_by_its_gate() -> None:
    """A gated setup step must name every stack whose template workflow uses it.

    The gates are hand-maintained name lists, so adding a stack of a language
    that needs a pinned toolchain is a second edit that is easy to forget. The
    failure is quiet: the setup step skips, the stack builds on whatever the
    runner image happens to carry (or not at all), and only that one shard goes
    red. Deriving the requirement from the template's own workflow keeps the
    guard honest for every language instead of the four that had a bespoke test.
    """
    gates = {
        match.group(1): _gated_by(f"uses: {match.group(1)}@")
        for match in _USES.finditer(CI.read_text(encoding="utf-8"))
    }
    problems = []
    for name, workflow in _template_workflows().items():
        for match in _USES.finditer(workflow.read_text(encoding="utf-8")):
            action = match.group(1)
            if action in _NOT_A_TOOLCHAIN or action not in gates:
                continue
            if not gates[action]:  # the step is unconditional: it runs for everyone.
                continue
            if name in _GATE_EXEMPTIONS:
                continue
            if name not in gates[action]:
                problems.append(f"{name} needs {action} but the gate omits it")
    assert not problems, "; ".join(sorted(set(problems)))


def test_every_stack_that_needs_a_pinned_runtime_is_gated() -> None:
    """The ruby/php/dotnet gates pin a version; ungated stacks get the image default.

    Each of these templates ships its own workflow that pins ruby 3.2-3.4, PHP
    8.3 or the .NET 8 SDK. A stack missing from the gate still passes locally and
    in `newstack check`, then runs on whatever the runner image happens to carry,
    so the two environments drift apart silently. Unlike the JDK gate there is no
    compiler error to catch it: the check just exercises a different runtime.
    """
    stacks = load_stacks()
    problems = []
    for language, marker in GATED_TOOLCHAINS:
        gated = _gated_by(marker)
        assert gated, f"ci.yml has no step using {marker}"
        missing = sorted(
            name
            for name, stack in stacks.items()
            if language in stack.requires and name not in gated
        )
        if missing:
            problems.append(f"{language}: {', '.join(missing)}")
    assert not problems, (
        "these stacks need a pinned runtime but no gate names them: " + "; ".join(problems)
    )
