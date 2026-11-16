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
x-shared-steps: &shared_setup     # the ~68 steps, once
  - uses: actions/checkout@v7
  ...

jobs:
  stacks-a:
    name: stack ${{ matrix.stack }} is green (a)
    strategy:
      matrix:
        stack: [ ... 79 entries ... ]
    steps: *shared_setup
  stacks-b: ...   # 79
  stacks-c: ...   # 78
  stacks-d: ...   # 78
```

One anchored step list feeds all four jobs. Do not inline copies: the 60-odd
toolchain gates (`if: contains(fromJSON([...]), matrix.stack)`) are the part
that rots first — a stack whose gate is missing from one copy fails only on
that shard.

Shards stay balanced (largest ≤ 2× smallest) so no single job becomes the long
pole; `tests/test_docs.py` enforces the cap, the balance, the uniqueness of the
union, and the single shared step list. Add a shard when a shard passes ~200
entries: 5 shards × 200 = 1,000 stacks still fits, and the 1,029-dummy-job probe
(plan task T3.4) is what proves the runner capacity before the tree gets there.

## Adding a stack

Until `scripts/wire_stack.py` lands (see the growth plan), add the entry to the
shortest shard by hand *and* the README table, then run
`uv run pytest tests/test_docs.py -q`: those guards are what catch a stack that is
in the registry but in no shard — invisible to CI, which is the failure mode this
file exists to prevent.
