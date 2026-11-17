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
