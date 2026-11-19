# CI: how the stack jobs are laid out, and the 256-job trap

`.github/workflows/ci.yml` runs four things:

| job | what it proves |
| --- | --- |
| `test` | the CLI itself under Python 3.10 – 3.13 (`ruff`, `pytest`) |
| `stacks-a` … `stacks-d` | each stack is really generated and its verify steps pass on a clean runner |
| `package` | the built wheel ships every stack and installs into a fresh venv |

## Why the stack job is sharded

GitHub expands **at most 256 jobs from one matrix**. A matrix with 257 entries
does not expand *partially* — it does not expand **at all**. No `stack <name>`
job is created, the job is reported as failed with no logs, and the run looks
like an ordinary red build. That is exactly what happened here between v0.4.0
(34 stacks) and the 314-stack tree: the single `stack:` matrix grew past 256,
the per-stack jobs silently disappeared, and ~58 stacks were never verified on
a runner while `main` stayed red.

Measure it instead of trusting the UI:

```sh
gh api repos/<owner>/newstack/actions/runs/<run-id>/jobs --jq .total_count
```

A healthy run counts one job per stacks entry **plus** the 5 non-matrix jobs
(1 `test` × 4 Python versions = 4 jobs, plus `package`) — e.g. 314 + 5 = 319 at
314 stacks. If the count equals the non-matrix total, the matrix did not expand.

## Layout

```yaml
jobs:
  changed:                         # did any stack change? (runs on every event)
    outputs: { stacks: ${{ steps.diff.outputs.stacks }} }
  stacks-a:
    name: stack ${{ matrix.stack }} is green (a)
    needs: changed
    if: needs.changed.outputs.stacks == 'true'
    runs-on: ubuntu-24.04
    strategy:
      matrix:
        stack: [ ... 79 entries ... ]
    steps: &shared_setup           # the ~71 steps, defined once, anchored here
      - uses: actions/checkout@v7
      ...
  stacks-b: ...   # 79
    steps: *shared_setup
  stacks-c: ...   # 78
  stacks-d: ...   # 78
```

The anchor must sit on the **first job's `steps:` key**. A top-level
`x-shared-steps: &shared_setup` looks tidier and silently breaks the whole
workflow: GitHub's schema drops unknown top-level keys, the aliases then resolve
to nothing, and the run reports zero jobs with "This run likely failed because
of a workflow file issue" (run 43883103545 is the example). Validate any anchor
edit by checking that the run's `total_count` is non-zero before believing it.

One anchored step list feeds all four jobs. Do not inline copies: the 60-odd
toolchain gates (`if: contains(fromJSON([...]), matrix.stack)`) are the part
that rots first — a stack whose gate is missing from one copy fails only on
that shard.

Shards stay balanced (largest ≤ 2× smallest) so no single job becomes the long
pole; `tests/test_docs.py` enforces the cap, the balance, the uniqueness of the
union, and the single shared step list. Add a shard when a shard passes ~200
entries: five shards × 200 = 1,000 stacks still fits under the cap. Measured on
the 314-entry layout: a per-stack job has a median of 23 s and a p90 of 29 s on a
warm runner, so the wall-clock cost of the matrix is the queue, not the work —
which is the other reason the nightly run and the PR gate above exist. The
1,029-dummy-job capacity probe (plan task T3.4) was dropped: the four real
shards already prove expansion (`total_count` = stacks + 5) and dummy jobs buy
no information the real ones do not.

## Triggers: push, a nightly run, and the pull-request gate

The workflow runs on three triggers, and each answers a different question:

- **`push` to `main`** — is the tree I just merged green? The whole matrix runs.
- **`schedule` (03:00 UTC daily)** — has a toolchain moved under us? A Go, Node,
  GHC or JDK release can break a stack with no commit of ours behind it, and a
  stack nobody scaffolds for a month is a stack we ship broken. The nightly run
  is the same four shards on the same anchored steps, so a nightly failure is a
  stack failure, not a different code path.
- **`pull_request`** — the `changed` job diffs the branch against its base and
  sets `stacks=true` when anything under `src/newstack/data/stacks/` moved. A
  docs-only or CLI-only PR then skips all four shards (the `test` and `package`
  jobs still run), while a PR that touches a stack still runs the full matrix:
  conservative on purpose, because the whole point is that a stack change is
  never verified by a subset.

`tests/test_docs.py` pins all of it: the `schedule` trigger exists, every shard
`needs: changed`, and every shard carries `if: needs.changed.outputs.stacks == 'true'`.
The gate is a `needs` + `if` pair rather than a `paths:` trigger on the workflow
because `paths:` would skip the unit tests and the wheel for a docs-only change too.

**Do not put the pull-request condition on the `changed` job itself.** A job whose
`needs` was skipped is skipped as well, even when its own `if` looks true, so
`if: github.event_name == 'pull_request'` on the gate turned a push run into a
green run with 10 jobs and no stack verified — the matrices never expanded and the
job names still contained the literal `${{ matrix.stack }}`. The condition lives on
the gate's *steps* (checkout and diff only run for a pull request); the job runs
on every event and answers `stacks=true` for push and schedule. Check the symptom
directly: a push run must have `total_count` = stacks + 6 — one job per stack, plus
the four unit-test legs, the gate job and the wheel job, so 320 at 314 stacks.

The dynamic alternative — one job computing the changed stacks and feeding
per-shard `fromJSON` matrices so a PR runs only what it touched — arrives with
the tree at ~500 stacks, when a full PR run costs more than the rewrite. It is
also what invalidates the static-matrix guards in `tests/test_docs.py` and the
shard-append logic in `scripts/wire_stack.py`, so it is one change, not two.

**Do not re-run an older run while a newer one is in flight.** The workflow keeps
`concurrency: ci-${{ github.ref }}` with `cancel-in-progress: true` so a push
supersedes the previous commit's 384-job run. A manual re-run of an *old* run joins
that same group as a fresh entry, so GitHub cancels whatever is running for the ref —
including the newer commit's run (it killed the wave-4 push run 51s in). Sequence
manual re-runs after the current run finishes, and check `gh run list` before firing
one.

**Treat a lone Maven failure as a registry flake, not a template defect.** Maven
Central intermittently answers 429 or omits an artifact that resolves seconds later.
Four separate red runs traced to this: `java-maven-cli` twice, `java-jdbc-sqlite-api`
(`HTTP Status: 429` on `org.xerial:sqlite-jdbc:3.46.1.3`), and — because they build
with `cache: maven` rather than Gradle — the two Kotlin stacks `kotlin-cli` and
`kotlin-ktor-api`, which download the Kotlin Maven plugin on every runner. The
discriminator is a local `newstack check <stack>`: if it passes, re-run the failed
job (after the in-flight run finishes, per the paragraph above) instead of editing
the template. Two Maven jobs failing in the same shard usually means one shared
download, not two broken projects.

The same rule covers a Clojure failure that gets past setup: in the wave-14 run both
`clojure-cli` and `clojure-ring-api` failed at `Generate and verify the stack` while
`Set up Java (clojure-cli)` and `Install the Clojure CLI` both succeeded, and both pass
locally (`clojure-cli` 6.8s / 7 steps, `clojure-ring-api` 4.0s / 2 steps). A first
`clojure` run in a fresh render fetches its own dependency tree from Maven Central, so
it shares the flake above; the shape to look for in the job steps is install green,
verify red.

## Runner image: the shards stay on 24.04

The stack shards pin `runs-on: ubuntu-24.04` while `test` and `package` float on
`ubuntu-latest`. `ubuntu-latest` moved to 26.04 and two toolchains in the shared
step list cannot run there:

- `swift-actions/setup-swift@v2` aborts with `Version "26.04" of Ubuntu is not
  supported` — swift-http-api and swift-cli never reach their verify step.
- `ocaml/setup-ocaml@v3` bootstraps through apt and 404s on
  `libc6-dev-i386_2.43-2ubuntu2.4`, so ocaml-http-api and ocaml-cli die in setup.

Pin the image rather than rewriting those installs; move the shards back to
`ubuntu-latest` when both actions publish 26.04 support (the failure is loud and
obvious if you try it early). Distro packages the smokes need but the image
does not carry are installed by stack-scoped gates in the shared step list:
`redis-tools` for python-resp-server, `mosquitto-clients` for python-mqtt-broker,
and `binutils`/`gcc`/`libgmp-dev` for the ghcup-based Haskell stacks (`cabal`
otherwise dies with `collect2: fatal error: cannot find 'ld'`).

## Toolchain gates, and the one that bit

Most toolchains come from a stack-scoped step in the shared list: `if: contains(fromJSON([...]), matrix.stack)`
or `if: matrix.stack == '<name>'`. A stack that needs a tool the runner image does not carry must be named
in the matching gate — and nothing fails loudly when it is not, because the stack's verify step simply runs
against the runner's default tool.

That is exactly how `java-picocli-cli` shipped red: it compiles with Maven at `release 21`, passed locally
on JDK 21, and died on the runner with

```
[ERROR] Failed to execute goal ...maven-compiler-plugin:3.16.0:compile ...:
        Fatal error compiling: error: release version 21 not supported
```

because the setup-java gate listed the other Maven stacks and not this one. Adding a Maven/Gradle stack
means adding its name to that gate; `tests/test_docs.py::test_every_java_build_stack_gets_a_runner_jdk`
now fails if a stack that requires `java` plus `mvn`/`mvnw`/`gradle`/`gradlew` is missing from every
`actions/setup-java` step. Interpreter-only JVM stacks (groovy, clojure, scala-cli) are exempt on purpose:
they need a JRE the image ships, not a compiler at a specific release.

`elixir-gen-server` shipped red the same way, one wave later: the runner image has no `mix` at all, the
setup-beam step that installs Elixir named only `elixir-mix-cli` and `phoenix-app`, and the job failed with

```
  elixir-gen-server SKIP  missing toolchain: mix
```

`tests/test_docs.py::test_every_elixir_stack_gets_a_runner_elixir` now fails if a stack requiring `mix` is
missing from every `erlef/setup-beam` step that pins `elixir-version:` (the Erlang/rebar3 and Gleam steps
are skipped by that check, so they do not accidentally satisfy it).

Ruby, PHP and .NET have the quieter version of the same failure. The image ships all three, so a stack
missing from `ruby/setup-ruby`, `shivammathur/setup-php` or `actions/setup-dotnet` does not error: it just
runs on an older default than the version its own workflow pins (ruby 3.2-3.4, PHP 8.3, .NET 8). That is
drift rather than a crash, and only the ruby gate is version-sensitive enough to notice locally — ruby-cli
needs 3.3, `ruby-hmac-webhook` runs on the stdlib and rake alone, so the no-bundler ruby step names both.
`tests/test_docs.py::test_every_stack_that_needs_a_pinned_runtime_is_gated` keeps all three gates honest:
every stack whose `requires` names `ruby`, `php` or `dotnet` must appear in a step that uses the matching
action.

## Adding a stack

```console
$ uv run python scripts/wire_stack.py <stack-name> --dry-run   # show the diff
$ uv run python scripts/wire_stack.py <stack-name>             # README row + shortest shard
$ uv run python scripts/gen_catalog.py                         # docs/STACKS.md
$ uv run pytest tests/test_docs.py tests/test_catalog.py -q
```

`wire_stack.py` is idempotent, refuses to push a shard past the 256-entry cap or
break the balance rule, and names a manifest that does not exist. Then run
`uv run pytest tests/test_docs.py -q`: those guards are what catch a stack that
is in the registry but in no shard — invisible to CI, which is the failure mode
this file exists to prevent.

## A template's own `ci.yml` is never run by this repo's CI

The workflows under `src/newstack/data/stacks/*/template/.github/workflows/ci.yml` only execute
inside a project created by `newstack new`. newstack's own matrix renders a stack, runs its
`verify` steps and its `smoke.sh`, and never reads the rendered workflow — so a template workflow
that builds the wrong binary or calls a subcommand the CLI does not have ships green and only
fails in the user's repository. Two real cases: eight Go stacks carried `go build -o bin/jsonlq .`
(copied from `go-jsonl-query`), and three Ruby CLIs carried the webhook verifier's `sign`/`verify`
steps, which exit non-zero because those CLIs have no such subcommand.

`tests/test_template_ci.py` now guards both shapes:

- `test_a_template_workflow_only_runs_its_own_binaries` — every `bin/<literal>` in a template
  workflow must also appear in the rest of that stack's template or in its `stack.json`; a name
  that appears nowhere else came from a copy-paste. Any legitimate self-built artifact
  (`bin/server.jar`) therefore has to be written with the `{{ npm_name }}` placeholder, which is
  the convention anyway.
- `test_ruby_rake_cli_stacks_share_one_workflow` — all rake-based Ruby CLI stacks must ship one
  identical workflow (syntax check, `rake test`, `bash smoke.sh`), so scaffolding any of them
  produces the same CI.

When you copy a workflow between stacks, change the parts that are about the *other* stack before
you commit: the binary it builds and the subcommands it calls.

## A toolchain gate is a name list, and it rots in both directions

The setup steps for the pinned toolchains (Ruby, PHP, .NET, Bun, Nim, Zig, Lua, Deno, Crystal) run
only for the stacks their `if: contains(fromJSON([...]), matrix.stack)` names. That list is a second
edit every time a stack of that language lands, and forgetting it fails quietly: the setup step
skips, `Generate and verify the stack` builds against whatever the runner image carries, and only
that one shard goes red. `bun-file-hash-cli` was added in wave 10 without being named, and the run
for that commit failed on exactly that job with `Set up Bun` marked SKIPPED.

`tests/test_docs.py::test_every_template_toolchain_is_named_by_its_gate` derives the requirement
from the templates themselves instead of a per-language map: for every `uses: owner/action@` in a
stack's template workflow, if this repo's ci.yml has a step for the same action that is gated by a
name list, the stack must be in that list. Two explicit exemptions keep it honest — `setup-go` and
`dtolnay/rust-toolchain` are satisfied by the runner image (every Go and Rust stack is green in a
run where the legacy list skipped them), and `erlang-cli` takes Erlang from the apt step rather
than the `setup-beam` step its template happens to use. Anything else that needs an exemption is a
gate that needs fixing, not a test that needs relaxing.

That guard only sees `uses:` steps, so the plain `run:` installers drifted invisibly: the Clojure
CLI, Tcl and Lua are installed by `run:` steps with the same `if: contains(fromJSON([...]))` shape,
and wave 16 added `clojure-cron-cli`, `tcl-base64-cli` and `lua-json-lite` without naming any of
them. Nothing goes red locally — the tool simply is not on that job's `PATH`.
`tests/test_docs.py::test_every_single_language_gate_names_every_stack_of_that_language` closes it
from the other side: a gate whose names all share one language prefix (`clojure-`, `tcl-`, `lua-`)
must name every stack of that language in the registry. Mixed gates (java + kotlin + clojure in one
list) are skipped because they are per-job capability lists, not language lists, and the two gates
that are deliberately narrower — the python protocol-client step and the no-bundle Ruby step whose
`ruby-sinatra` rides the bundler step above it — are named exemptions.
