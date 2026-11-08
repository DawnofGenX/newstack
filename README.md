# newstack

[![CI](https://github.com/DawnofGenX/newstack/actions/workflows/ci.yml/badge.svg)](https://github.com/DawnofGenX/newstack/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/newstack)](https://pypi.org/project/newstack/)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![dependencies](https://img.shields.io/badge/runtime%20dependencies-0-brightgreen)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**Scaffold a new project on any popular stack — and every starter it emits is proven green in CI.**

```console
$ newstack new python-lib ~/code/mylib
newstack 0.1.0  ·  python-lib  →  /home/you/code/mylib

  created       8 files
  git           initialised on main, first commit made

  next:
    cd /home/you/code/mylib
    uv sync
    uv run pytest
```

## Why this exists

`cookiecutter`, `copier`, `yeoman`, `degit`, `npm create …` and `gh repo create --template`
all solve *part* of the problem. Two things are still missing in practice:

1. **One tool for every stack.** Python templates are Python-only, JS templates are
   JS-only, and `gh repo create --template` clones a whole repository with no variables.
2. **A guarantee that the template still works.** Templates rot silently. You find out
   the starter is broken *after* you have already started building on top of it.

`newstack` fixes both. It is one zero-dependency CLI that carries a curated stack
registry, and **every stack in that registry is generated and checked on every push**
(`newstack check --all` in CI). If a starter breaks, the badge goes red — not your
first day of work.

## Install

```bash
uvx newstack list          # run without installing
uv tool install newstack   # or put it on your PATH
pipx install newstack      # any of the usual runners works
```

From a clone:

```bash
git clone https://github.com/DawnofGenX/newstack && cd newstack
uv sync && uv run newstack list
```

## Use

```bash
newstack list                       # what is available, and what each stack needs
newstack new react-vite-ts ~/code/app
newstack new fastapi ~/code/api -d "Billing service" --author "Your Name"
newstack new python-lib ~/code/lib --dry-run     # preview, write nothing
newstack new python-cli ~/code/tool --github     # create the repo and push it too
newstack new fastapi ~/code/api --python 3.12    # raise a Python stack's floor
newstack new react-vite-ts ~/web --node 24       # and a JavaScript stack's
newstack new react-vite-ts ~/web --package-manager pnpm  # npm (default), pnpm, yarn
newstack stacks outdated            # which installed stacks moved upstream
newstack stacks update              # re-pull every stack you installed from a repo
newstack new python-lib ~/code/lib --license apache-2.0   # mit (default), apache-2.0, bsd-3, none
newstack adopt ~/code/old-project --dry-run    # retrofit CI/lint onto existing code
newstack update ~/code/app --dry-run   # re-apply template changes, keep your edits
newstack outdated ~/code/app         # what has the template moved on from?
newstack check --all                # prove every stack on this machine
newstack doctor                     # which toolchains do I have?
newstack stacks add <git-url>       # install a stack that is not shipped here
```

Every command takes `--json` where it makes sense, so the tool is scriptable.

`newstack new` renders variables, initialises git with a first commit, and (with
`--github`) creates the remote repository and pushes — one command from empty
directory to CI-ready project.

### Choosing a licence

Every project gets a `LICENSE` file, and `--license` decides which one:

```console
$ newstack new rust-cli ~/code/scanner --license apache-2.0
$ head -2 ~/code/scanner/LICENSE
                                 Apache License
                           Version 2.0, January 2004
```

The choices are `mit` (the default), `apache-2.0`, `bsd-3`, and `none` for no
file at all. The text comes from `src/newstack/data/licenses/`, is filled with
your `--author` and the current year, and is the same for every stack — a
template's own `LICENSE` is never trusted over it. The choice is stored in
`.newstack.json`, so `newstack update` keeps writing the licence you picked;
`newstack update --license bsd-3` switches it later. `newstack adopt` never
touches `LICENSE`: retrofitting CI onto existing code must not relicence it.

### Choosing the interpreter

The Python stacks declare which interpreters they have been proven on, and
`--python` picks a floor from that list:

```console
$ newstack new fastapi ~/code/api --python 3.12
$ grep -E 'requires-python|target-version' ~/code/api/pyproject.toml
requires-python = ">=3.12"
target-version = "py312"
```

One value writes every line that names a version: `requires-python`, the ruff
target, the trove classifiers, the `python-version` matrix in the generated
workflow, the `FROM python:` tag in the Dockerfile, and the README's "requires"
line. That is the point — the versions CI runs and the version the package
promises cannot drift apart, because nothing in the template hard-codes them.
The floor can only go **up**, and only to an interpreter the stack was proven
on: `--python 3.9` on `python-cli` and `--python 3.10` on `django` (which needs
3.12) are both refused before anything is written. Stacks that are not Python
say so rather than silently ignoring the flag. The choice is recorded in
`.newstack.json`, so `newstack update` keeps the floor your project declares;
`newstack update --python 3.13` moves it later, and every affected file
follows.

### Choosing the Node major

The JavaScript stacks do the same thing with majors. `--node` moves the floor,
and `engines`, the CI matrix and the README are all rendered from it:

```console
$ newstack new react-vite-ts ~/code/web --node 24
$ grep -A2 engines ~/code/web/package.json
  "engines": {
    "node": ">=24"
  }
$ grep node-version ~/code/web/.github/workflows/ci.yml
        node-version: ["24"]
```

The matrix shrinks with the floor: asking for 24 on a stack proven on 22 and 24
runs 24 alone, because a leg on a version you no longer claim to support is not
a test. `astro` declares 24 as its own minimum — Astro 7 refuses to start on
anything older — so `--node 22` there is an error rather than a broken project.
As with `--python`, the floor can only go up, `newstack update` keeps the one
your project declares, and `newstack update --node 22` moves it back down only
if the stack still supports that major.

### Choosing the package manager

The JavaScript stacks declare the managers they have been proven with, and
`--package-manager` writes that manager into every command the project carries:

```console
$ newstack new react-vite-ts ~/code/web --package-manager pnpm
...
  next:
    cd /home/you/code/web
    pnpm install
    pnpm run dev

$ grep -E "Prepare|run: pnpm" ~/code/web/.github/workflows/ci.yml
      - name: Prepare pnpm
        run: npm install -g pnpm@10 && pnpm --version
      - run: pnpm install
      - run: pnpm run typecheck
      - run: pnpm test
      - run: pnpm run build
```

One value writes the install, the test, the run and the build lines in the
workflow and the README, the lockfile the README tells you to commit
(`pnpm-lock.yaml`), the `cache:` hint for the CI setup step, the `Prepare ...`
step that installs the manager itself before it is used, and — where the template
ignores one — the manager's debug log in `.gitignore`. Nothing in the template
hard-codes `npm` any more, so a project cannot end up half-migrated with an `npm`
command in a `pnpm` workflow.

Only the managers a stack was proven with are accepted: `--package-manager bun`
on `react-vite-ts` and any `--package-manager` on a non-JavaScript stack are
refused before anything is written. The choice is recorded in `.newstack.json`,
so `newstack update` keeps the manager your project uses, and
`newstack update --package-manager yarn` switches it later — install, test,
build, lockfile name and README all move together.

### Stacks from outside this repository

The stacks that ship in this repository are the ones CI proves. `stacks add`
installs one from anywhere else, and says plainly that it is not covered by that
promise:

```console
$ newstack stacks add https://github.com/you/newstack-stacks
installed 1 stack from https://github.com/you/newstack-stacks

  elixir-cli  /home/you/.local/share/newstack/stacks/elixir-cli  (9f2c1ab)

  These are not covered by newstack's CI — prove one here with:
    newstack check elixir-cli

  scaffold one:  newstack new elixir-cli <path>
```

A repository may carry one stack at its root, a stack per directory, or a
`stacks/` directory of them; `--dir` says where to look. Every stack in the
repository is validated before any of them is written, so a repository with one
broken manifest installs nothing, and a name that already ships with `newstack`
is refused rather than shadowing it. `--force` replaces an installed stack
wholesale, `newstack stacks remove <name>` deletes one, and `newstack stacks list`
shows what came from where. Installed stacks live in `$NEWSTACK_HOME/stacks`
(default `~/.local/share/newstack/stacks`), are marked `[installed]` in
`newstack list`, and behave like any other stack afterwards — `new`, `adopt`,
`update` and `outdated` all see them.

`newstack stacks update` re-pulls them, so a fix in the stack's repository
reaches your machine without reinstalling by hand:

```console
$ newstack stacks update
  elixir-cli  9f2c1ab → 4d0b7e2  updated

  1 stack refreshed (elixir-cli)
  projects generated from them pick this up with:  newstack update <path>
```

The clone, the validation and the name checks all happen before anything is
replaced, so a repository that went bad — or one that dropped a stack — leaves
your installed copy exactly as it was and says which stack it could not find.
`newstack stacks update <name>` does one. Refreshing a stack changes the
template, not your projects: `newstack update <path>` is still the step that
re-applies it, and it keeps the local edits it finds.

`newstack stacks outdated` answers the same question without cloning: it asks
each repository for the commit on its default branch and compares that with the
revision recorded at install time, so a check costs one round trip per stack.
It exits 1 when something is behind — and reports an origin it could not reach
as "could not check" instead of hiding the stacks whose state it does know.

```console
$ newstack stacks outdated
  elixir-cli  9f2c1ab → 4d0b7e2  behind

  1 stack behind upstream:  newstack stacks update
```

## Stacks

| Stack | What you get | Toolchain |
| --- | --- | --- |
| `python-lib` | src layout, hatchling build, pytest, ruff, 4-version CI matrix | `uv` |
| `python-cli` | console entry point on argparse, zero runtime deps, tested CLI | `uv` |
| `fastapi` | typed JSON API, pydantic models, TestClient tests, Dockerfile | `uv` |
| `django` | Django 6.1 app: config/core split, SQLite, pytest-django, migration drift check | `uv` |
| `flask` | Flask app factory: JSON routes, pytest fixtures, ruff, CI | `uv` |
| `python-fastapi-sqlite` | FastAPI over SQLite: numbered SQL migrations applied in `lifespan`, WAL + busy timeout on every connection, typed request models, restart-safe rows | `uv` |
| `python-sse-api` | Server-sent events: an endless `text/event-stream` response, `Last-Event-ID` resume, proxy-proof headers, and a socket test that fails if the body is buffered | `uv` |
| `python-scheduler-api` | A durable scheduler: due jobs claimed under `BEGIN IMMEDIATE`, interval jobs rescheduled from *now* so an overdue job does not stampede, exponential back-off capped by `max_attempts`, and a run ledger with the counts of every attempt | `uv` |
| `python-webhook-receiver` | Signed webhooks: HMAC-SHA256 over the *raw* body (a parsed and re-serialised body never matches), a both-directions replay window, `hmac.compare_digest`, idempotency enforced by an event-id primary key, and a 401 before any parser sees the payload | `uv` |
| `python-litestar-api` | Litestar 2 text-statistics API: the handler takes `Request` instead of a validated parameter so `422` stays the project's answer, `raw_path` already carries the query string, and every rule lives in a pure `route()` function with a TestClient suite on top | `uv` |
| `python-eval-harness` | Offline eval harness: JSONL gold + predictions, `exact_match`/`token_f1`, a missing prediction scores zero instead of shrinking the denominator, and `compare` exits 1 on a per-example regression | `uv` |
| `python-batch-inference` | Resumable batch inference over any OpenAI-compatible endpoint: JSONL in and out, bounded concurrency, exponential back-off on 408/429/5xx only, a failure recorded instead of raised, and a rerun that skips ids already answered — proven by a stub server that answers 429 twice and 400 forever | `uv` |
| `python-duckdb-report` | DuckDB reporting CLI over CSV/Parquet: money summed as `DECIMAL` so `0.10 + 0.20` is `0.30` and not `0.30000000000000004`, null metrics counted and reported instead of dropped, groups ordered by total then name so the file diffs cleanly, identifiers checked against `DESCRIBE` before they are interpolated into SQL, and a golden `expected/report.md` compared byte for byte | `uv` |
| `python-migrations` | SQL migrations applied exactly once: every run records the sha256 of the file it applied, so editing an applied migration fails with `drift` instead of leaving the database and the repository quietly different; each file runs in one explicit transaction (`isolation_level=None`, because `executescript` commits behind your back) and statements are split with `sqlite3.complete_statement`, so a trigger body full of semicolons stays one statement | `uv` |
| `python-pdf-report` | NDJSON in, a deterministic PDF out: `rl_config.invariant = 1` is set before the first canvas so two runs are byte-identical, WinAnsi strips what cp1252 cannot hold and the count of replaced characters is printed, bytes are counted over UTF-8 so `héllo` is 6 bytes and 5 characters, and every build is read back with pypdf to prove the rows and the totals really reached the page | `uv` |
| `python-property-tests` | Half-open interval arithmetic checked by Hypothesis: invariants instead of examples, `derandomize=True`/`database=None`/`deadline=None` so a green build stays green, a stateful machine that applies random add/remove sequences to the code and a `set[int]` oracle, and a shrinking demo that reports the smallest input which fools a naive sum | `uv` |
| `python-openapi-client` | The OpenAPI document as the contract: a stdlib-only client validates the request body before it is sent and every response against the schema attached to that exact status, so an undocumented status or a drifted member fails at the call site — `bool` is named before `int`, path values are percent-encoded, a documented 4xx is a normal answer, and `validate --response` checks a saved body with nothing running | `uv` |
| `python-rag-eval` | Retrieval numbers that survive review: overlapping chunk windows with stable `doc#offset` ids and a coverage check, BM25 whose idf stays strictly positive so a stop word cannot push a chunk down, metrics computed over documents rather than chunk hits with precision divided by `k`, unjudged queries reported as `skipped` rather than scored zero, macro and micro recall side by side, and a `compare` gate that exits 1 when a change makes retrieval worse | `uv` |
| `python-pytest-plugin` | A pytest plugin as the product: a `ticket` marker registered so `--strict-markers` accepts it, a JSON report recording every phase of every test in milliseconds, `--testmeta-strict` refusing a suite with unmarked tests at collection (exit 4), and a `summary` command whose `--fail-over-ms` gate exits 1 when a test grows past its budget | `uv` |
| `python-config-precedence` | Layered configuration that can answer *why is the port 9200 in prod*: one schema table declaring every key with its kind, bounds and secrecy, a fold over `defaults < TOML file < environment < --set flags` rather than a chain of `if`s, provenance for every value naming the exact layer and raw location it came from, all problems reported in one run because layers are read before they are parsed, secrets masked in `show`, in `get` (which refuses without `--reveal`) and in the JSON payload, `__` nesting because `_` is legal inside a name, and a `check --strict` gate that exits 1 while a secret still holds the value that shipped with the code | `uv` |
| `python-task-queue` | A SQLite-backed job queue whose delivery guarantee is written down rather than assumed: at-least-once through single-statement leases (`UPDATE … RETURNING`), capped exponential backoff on retry, a heartbeat that opens its own connection inside its own thread, and a dead-letter state instead of a silent delete | `python` |
| `python-circuit-breaker` | A circuit breaker whose state machine is the product: consecutive-failure counting, a cooldown measured on an injected clock, exactly one half-open probe with a restart on the failed probe, an ignored-error classifier that still releases the probe, and counters for refused, late and tripped requests | `python` |
| `python-money-allocation` | Money as an integer count of minor units with its currency code carried alongside, so a float cannot enter and `Money(12.5, "USD")` is a `TypeError`: `parse('12.345 USD')` raises until a rounding mode is named (`half-even`/`half-up`/`down`/`up`), a decimal comma is refused rather than read as a thousands separator, and `allocate()` floors every share before handing the leftover units to the largest fractional remainders — so `100.00` in thirds is `33.34 + 33.33 + 33.33` and every split is summed and checked before it is returned | `python` |
| `python-rate-limiter` | A token bucket in integers: GCRA stores one number per key (the theoretical arrival time in scaled microseconds), so `100 a minute` really is a hundred at once and then one every 0.6 s instead of a float that drifts, `--limit 7 --per 60` reports a retry of exactly `8 571 429 µs`, a `Retry-After` is derived from the stored arrival time rather than added to the last failure, `reset_at` says when the bucket is full rather than when the next request fits, a cost above the burst is a configuration error and not a denial, refilled keys are pruned on a schedule so a table of IPs cannot grow forever (`max_keys` as the hard ceiling), the clock is injected so a boundary test is `499 999` denied / `500 000` allowed instead of flaky, and eight threads spending one bucket get exactly its burst — `check --repeat N` exits `1` when the limit is finally hit | `python` |
| `python-audit-log` | An append-only, hash-chained audit log where the detection is the tested part: every event hashes its canonical body plus the previous event's hash, so an edit (`body-changed` at its own row and nowhere else), a deletion (`gap` plus the broken link) and a `BEGIN IMMEDIATE` sequence that cannot fork are all named problems rather than an empty `ok`; a canonical form that refuses floats because `1.0` prints as `"1.0"` in Python and `"1"` in JavaScript; `--detail k=v` records a string while `--detail-json` keeps the type; and a checkpoint taken outside the log catches the attack a chain cannot see — the attacker who recomputes every hash — with `demo` exiting `1` while that scenario is still missed | `python` |
| `python-feature-flags` | Feature flags whose answers are reproducible: buckets come from SHA-256 over `salt:user` rather than `hash()` (which Python re-seeds per process, so a rollout written with it moves every user on every restart — a test runs the same script under three `PYTHONHASHSEED` values and a negative control shows `hash()` moving), percentages are integers with the cutoff in basis units so 0% admits nobody in a thousand and 100% admits everybody, each flag carries its own salt so two rollouts are independent experiments, the precedence table is kill switch > targeting > rollout with the winning rule named in the reason (`on  targeted` at 0% is not `on  inside`), an unknown flag is a reason rather than a traceback, and `distribution --users N` measures the rollouts it claims — worst deviation printed | `python` |
| `python-keyset-pagination` | Pagination that cannot skip or repeat a row: a cursor carries the sort position, and the demo shows what LIMIT/OFFSET costs. | Python 3.12+, no runtime dependencies |
| `python-outbox-pattern` | Transactional outbox: the order row and its event commit in one transaction, and the demo proves a crash between publish and mark costs a duplicate, not an event. | Python 3.12+, no runtime dependencies |
| `python-schema-evolution` | Schema diff that proves itself: every breaking change is shown by a real document that passed the old schema and fails the new one, and reader-only changes are labelled instead of faked. | Python 3.12+, no runtime dependencies |
| `python-idempotency-keys` | Idempotency keys over SQLite: claim the key, run the effect, store the answer, and replay it byte-for-byte on retry — with a lease that fences a stale attempt and a demo that counts effects, not answers. | Python 3.12+, no runtime dependencies |
| `python-counter-rollup` | Fold monotonic counter readings into floor-aligned windows: restarts counted as restarts (not negative deltas), missing scrapes that stay unknown, duplicate-safe merges of at-least-once rollups, and a rate that divides by observed time. | Python 3.12+, no runtime dependencies |
| `python-single-flight` | A TTL cache where concurrent misses for one key run the loader exactly once: one registry lock per lookup (never held across the load), waiters on their own key's event, failures broadcast but never cached, the TTL starting when the value became readable, and injected threads and clock so the stampede is reproducible instead of flaky. | Python 3.12+, no runtime dependencies |
| `python-text-diff` | A unified diff that proves it can be applied: every hunk is remeasured against the text it lands on (so a drifted hunk still applies and the report says where), a hunk that matches twice is an error rather than a coin flip, fuzz is reported and keeps the file's line instead of the patch's, the missing-final-newline marker round-trips, bytes are read and written so CRLF survives, and `check` computes `apply(old, diff(old, new)) == new` instead of asserting it. | Python 3.12+, no runtime dependencies |
| `python-html-sanitizer` | An allowlist sanitizer that rebuilds markup instead of filtering it: script bodies dropped with their content, URL schemes compared after the whitespace stripping a browser does, attributes limited per tag, broken nesting repaired, escaping done on write, the result proven to be a fixed point, and an audit that scans the OUTPUT for dangerous constructs. | Python 3.12+, no runtime dependencies |
| `python-cron-schedule` | A cron expression evaluator that answers the only question that matters at 03:00: which UTC instants does it fire at, in a named zone? Day-of-month and day-of-week are joined with OR when both are restricted (the Vixie rule), a local time DST skips has no run that day, a local time DST repeats runs twice, and a naive timestamp is refused because the whole subject is which zone a wall clock belongs to. | Python 3.12+, no runtime dependencies |
| `python-retry-budget` | An SLO of 99.9% is a budget of one bad event in a thousand. This turns bucket counts into that budget, its burn rate, and a two-window page rule: the long window says something is wrong, the short one says it is still wrong. Missing buckets are reported as missing rather than counted as good, and a window with no traffic has no burn rate at all instead of a reassuring 0.00x. | uv, Python 3.12+ |
| `python-permission-model` | An authorisation decision you can read out loud: which role the subject holds on this resource, which rule won, and why every other rule lost. Deny outranks allow, a role only applies inside its assigned scope, `*` matches one segment and `**` any number of them, and a condition about an attribute nobody sent is not a match. The policy is validated before it answers: cycles, unknown roles and duplicate rule ids are errors. | uv, Python 3.12+ |
| `python-saga-compensation` | A saga of local transactions with a compensation each, and the journal that makes it survive a crash: steps go forward, compensations in reverse, every attempt is appended and fsynced before its outcome is known. One failing compensation does not stop the rest, a succeeded step with no compensation makes the rollback *incomplete* instead of pretending, and an interrupted step is retried with the same idempotency key rather than assumed to have worked. | uv, Python 3.12+ |
| `python-time-series-window` | A windowed aggregate that admits what arrived late: half-open windows aligned to the epoch, a watermark derived from `max(event time) - lateness` so a replay is deterministic, and a buffer that keeps a window open until that watermark closes it — an event late but inside the allowance still counts, an event after it is reported as `too_late` and never rewrites an emitted number. Windows with no events are listed as missing rather than emitted as zero, and the mean of nulls stays undefined. | uv, Python 3.12+ |
| `python-dependency-resolver` | A version resolver that explains itself: semantic versioning with build metadata ignored in precedence, ranges (`^`, `~`, `x`, `*`, comparator lists, `||`) that never opt into a prerelease unless the range names one, and a backtracking search that visits the most constrained package first so the answer does not depend on root order. Every dead end is kept as an explanation, an unsatisfiable set names the conflicting ranges instead of printing a best-effort tree, and the lock is audited by re-resolving with it rather than by comparing versions. | uv, Python 3.12+ |
| `python-crdt` | Replicated state whose merge function is checked instead of assumed: a grow-only counter and the paired counter that replaces the signed max (shown losing a delayed decrement), a last-write-wins register that reports the write it drops and refuses two values under one stamp, and an observed-remove set where every add carries its own `(node, counter)` tag so a remove only deletes what it actually saw. Idempotence, commutativity and associativity run over real states — including merges that deliberately fail them — and a shuffled, duplicated gossip run is what proves the replicas converge. | uv, Python 3.12+ |
| `python-bloom-filter` | Membership tests sized from the budget: bits = -n·ln p / (ln 2)² and k = m/n·ln 2, with the arithmetic printed next to the answer. The one real guarantee (no false negatives) is checked against every item that was added; the false-positive rate is measured against the formula at three budgets; a k sweep shows the rate climbing on both sides of the textbook choice; clearing an item's bits is shown making a second item disappear, and the saturating counting filter is shown surviving the same removal. `info` reports fill, the item estimate and the predicted rate, and exits non-zero once the filter is past any use. | uv, Python 3.12+ |
| `python-consistent-hashing` | A hash ring whose claims are measured, not asserted: the same 5,000 keys through `hash % N` move 83.6% when a node joins while the ring moves 18.1% (one share); removal is proved to take only the departing node's keys, insertion order is proved not to matter, and wraparound is found rather than assumed. The vnode table prints the arc imbalance from the point spacing beside the measured key imbalance, because past ~160 points the 5,000-key sample is the limit and one "imbalance" number hides that. `move` fails when a key lands on a node that was already there or when more than 1.5x the fair share moves. | uv, Python 3.12+ |
| `python-leases-fences` | A lease and the fence that makes it mean something. The store grants one lease at a time with a strictly increasing token, renews from *now* rather than from the old expiry (extending from the deadline pays a paused holder for time it never used), and treats only its own clock as the authority. The resource compares tokens and refuses any write older than the last one it accepted, so the demo can run the same pause against a fenced and an unfenced value: the fenced one keeps `b-1`, the unfenced one keeps the ghost write `a-late` and prints it as a lost update. `model` exits 1 if the fence ever accepts a stale token and refuses a pause shorter than the lease. | uv, Python 3.12+ |
| `python-count-min-sketch` | An estimate with its error attached. The sketch answers "how many times did this item arrive?" from `width x depth` counters, and the demo measures the promise on a 125,652-update skewed stream with a known truth: zero underestimates, largest overestimate 211 against a bound of 1,334 at 256x5, and a table showing four times the width cutting the mean overestimate 57x. Merging two halves is proved to equal one pass row for row, conservative updates are compared against plain ones on identical input (mean 11.39 vs 34.87), and depth is capped at 8 because one blake2b digest can only supply that many rows. | uv, Python 3.12+ |
| `python-hyperloglog` | Cardinality estimation whose promise is measured. The sketch counts distinct values from a fixed bag of registers and prints the promised error (1.04/sqrt(m)) beside every estimate; the demo checks that promise at 100, 1,000, 10,000 and 100,000 distinct values, shows two halves merging into byte-identical registers with one pass, and proves 90,000 duplicate adds move nothing. It also measures its own failure mode: reading the index from the low bits of a hash that keeps structure there collapses 10,000 distinct values into 1 of 4,096 registers, and the precision table prints registers, memory, promised error and measured error side by side. `estimate --expect N` exits 1 when the error is outside four standard errors. | uv, Python 3.12+ |
| `python-backoff-jitter` | A retry simulator that measures the pile-up each backoff policy creates, instead of assuming jitter helps. | uv, Python 3.12+ |
| `python-hybrid-clock` | Wall time that never runs backwards. A hybrid logical clock keeps the highest physical millisecond it ever issued and a counter inside it, so a wall that steps back cannot move a stamp, a receipt can never sort before its send, and the node name finishes the order. `demo` runs six stories with the real numbers (a 400 ms step back, a 500 ms fast node, two orders disagreeing on the same events, a three-node exchange); `plan` replays a JSONL file of events and prints per-node skew, the wall-versus-stamp inversions and the causal breaks, exiting 1 when `--max-skew` is passed or causality breaks. | uv, Python 3.12+ |
| `python-json-patch` | RFC 6901 pointers and RFC 6902 patches that refuse to guess. A pointer is parsed with its two escapes, so a key holding a slash or a tilde stays one key; a segment that looks like a number is an object key when the parent is an object, and `-` can be written to but never read. Every patch is applied to a copy and discarded if one operation fails, so a failing `test` rolls back the operations around it and leaves the document byte-identical; `diff` produces a patch and then applies it, printing whether the result matches the document it was taken from. | uv, Python 3.12+ |
| `python-url-signing` | Signed requests over a canonical form instead of a raw URL: percent escapes are decoded and re-encoded in uppercase so `%7E` and `~` agree while a plus and a space do not, query parameters are sorted so reordering a request does not break it, and path segments are canonicalised separately so an escaped `%2F` stays data. The signing string is one fact per line, the body is covered by its hash, and a signature carries an expiry and a nonce, so a replay is refused and every refusal names the rule that failed. | uv, Python 3.12+ |
| `python-merkle-proofs` | Merkle inclusion proofs whose two hash inputs can never be confused: a leaf is hashed with a `0x00` prefix and a node with `0x01`, so a node's digest is not a valid leaf digest and the classic second-preimage forgery stops working. The tree splits at the largest power of two below the leaf count, so the shape is a rule and not a choice; a proof carries one sibling per level (the count depends on the index, because the RFC shape is not level) and is bound to its index, its size and its root. The demo measures the forgery, a tampered leaf, a moved index and two competing shapes. | uv, Python 3.12+ |
| `python-ab-test` | A/B tests where the p-value is not the whole story: a two-proportion test with a Wilson interval per arm, a difference interval and a relative lift that says what it cannot see; a sample-ratio-mismatch gate that exits 1 before anybody reads the lift; and a peeking simulation that MEASURES the same simulated worlds through one look, a flat 5% line at every look and an O'Brien-Fleming spending boundary (18.90% against 6.70% at 1000 trials), so the inflation and the repair are numbers rather than advice. | uv, Python 3.12+ |
| `python-minhash-lsh` | Near-duplicate detection whose error is predicted before it is measured: a MinHash signature agrees on each position with probability equal to the Jaccard similarity of the shingle sets, so the estimate carries a binomial error of 1/sqrt(width); banding turns that signature into a candidate set whose false-negative rate follows an S-curve you choose, every candidate is verified before two documents are called the same, and the demo prints the predicted curve beside the recall it actually got (77 candidates for 19,900 pairs, 99.6% never compared). | uv, Python 3.12+ |
| `python-lru-cache` | Four replacement policies (FIFO, LRU, CLOCK, segmented LRU) on seeded traces, with scan resistance and the frequency ceiling beside every hit ratio | uv, Python 3.12+ |
| `python-version-vectors` | Causal order as a partial order: per-writer counters, four verdicts, a merge that is a join, causal delivery that holds a message until its dependencies arrive, and compaction measured for where it is exact. | uv, python3 |
| `python-hdr-histogram` | Percentiles with a promised error: bucket-indexed latencies whose relative error is bounded and measured, merges that are exact, memory that depends on the value range and not on the sample count, and the average-of-percentiles trap printed side by side with the truth. | uv, python3 |
| `python-snowflake-ids` | Time-ordered identifiers whose layout is a promise: 41 bits of milliseconds, 10 bits of worker, 12 bits of sequence, a clock that must not go backwards, a sequence that must not wrap silently, and capacity numbers you can check instead of trusting. | uv, python3 |
| `python-semver-ranges` | A version range as a union of intervals: caret, tilde, hyphen, wildcard and comparator ranges, prereleases that are opt-in per core, intersections that can be proven empty, and a decision that explains every arm that refused. | uv, python3 |
| `python-gitignore-matcher` | An ignore file read the way git reads it: anchored versus bare patterns, directory-only rules, the last matching rule winning, and the ancestor rule that makes a negation useless — with the deciding line named. | uv, python3 |
| `python-rrule-recurrence` | A recurrence rule expanded into instants: COUNT counts firings, UNTIL is an inclusive instant, INTERVAL is anchored to the start's period, ordinal weekdays count from the month's edges, and a wall time the zone skipped is reported instead of guessed. | uv, python3 |
| `python-three-way-merge` | A three-way merge that conflicts only the region both sides changed: an identical edit is agreement, two insertions at one point conflict because the base orders nothing, an insertion beside a replacement stays separate, markers always own their line, and every chunk is explained before the text. | uv, python3 |
| `python-linearizability-checker` | A register history decided rather than sampled: the search respects each client's programme order and the real-time order together, a witness order is replayed value by value, a refusal comes with a core that cannot shrink, and the pruning is measured against every permutation. | uv, python3 |
| `python-expression-parser` | Arithmetic parsed by precedence climbing and printed back exactly: parentheses appear only where they change the tree, exact mode refuses answers that need rounding, and every error names the column it is about. | uv, python3 |
| `python-route-trie` | A route table you descend instead of scanning: literals beat parameters, parameters beat catch-alls, a dead branch is abandoned rather than fatal, and a wrong method reports the methods that would have worked. | uv, python3 |
| `python-regex-engine` | A pattern compiled to a Thompson NFA and simulated as a set of states, so matching costs one pass and never backtracks; the same pattern is determinised and both machines are proved equal by enumeration. | uv, python3 |
| `python-bk-tree` | Edit distance plus a Burkhard-Keller tree: a word is found by distance without comparing it to every word, and the pruning is proved against a full scan on the same corpus. | uv, python3 |
| `python-skip-list` | A sorted map that balances on seeded coin flips instead of rotations: insert, delete, rank, and select cost one walk, link widths are repaired on every edit, and rank answers exactly what bisect answers. | uv, python3 |
| `python-b-tree` | A keyed B-tree of configurable order: insert with splits, delete with borrow and merge, exact lookup and range scan, and a page file that reads back identical after any history. | uv, python3 |
| `python-lsm-tree` | A log-structured merge table of integer keys and string values: a sorted memtable flushes to numbered on-disk level tables, reads fall through newest level first, and compaction merges sorted tables while dropping tombstones. | uv, python3 |
| `python-interval-tree` | A centered interval tree over half-open integer spans: stabbing and overlap answers equal the brute-force scan on any seeded corpus, the max-end augmentation is repaired on every delete, and a point at a span's right end stands outside it. | uv, python3 |
| `python-aho-corasick` | Multi-pattern matching in one pass: a trie with BFS failure links, suffix outputs that never miss an overlap, and a hit set proven equal to a naive scan on seeded alphabets. | uv, python3 |
| `python-radix-heap` | An integer min-heap that never compares keys: buckets follow the keys' bits, pop-min drains sorted on monotone and mixed streams, and the bucket invariant is re-checked after every op against the sorted corpus. | uv, python3 |
| `python-scapegoat-tree` | A binary search tree that rebuilds instead of rotating: the 0.7 alpha rule decides every repair, depth stays under log base 1/alpha of n, rebuilds are lossless against bisect, and the work counter settles at n log n. | uv, python3 |
| `python-union-find` | A disjoint-set forest over integer elements: union by size keeps depth logarithmic, find compresses on the way back, and the partition equals a dict-of-parents reference after any seeded workload. | uv, python3 |
| `python-fenwick-tree` | A binary indexed tree over integer values: point adds climb the lowest bit, prefix and range sums walk it back, and every answer is checked against the running list-sum reference the walk visits at most bit-length(n) cells. | uv, python3 |
| `python-binomial-heap` | A mergeable integer min-heap of binomial trees: a tree of rank k holds exactly 2^k keys, the forest keeps one tree per rank, size follows the bit pattern of the count, and meld unions two heaps -- what plain heaps refuse. | uv, python3 |
| `python-prefix-trie` | A string-keyed trie over lowercase words: membership answers equal a set's, every prefix listing equals the sorted scan of the corpus, delete drops only the exact word, and the empty prefix lists every word exactly once. | uv, python3 |
| `python-kd-tree` | A 2-d kd-tree over integer point pairs: membership answers equal a set's, a rectangle answer equals the brute-force filter, the nearest answer equals the brute-force argmin with the tie on the lexicographically smallest point, and a rebuild from the in-order walk answers identically. | uv, python3 |
| `python-suffix-array` | Sorted suffix starts of a lowercase text: the order equals the slice-sort exactly, every count equals the scan's start census with overlaps honest, and the longest repeat is the tallest neighbour share. | uv, python3 |
| `python-avl-tree` | A height-balanced BST over integer keys: the walk equals sorted(live) on mixed insert/delete storms, every balance factor stays inside -1, 0, 1 after every move, rotations preserve the walk, and the height stays under the AVL ceiling. | uv, python3 |
| `python-red-black-tree` | A red-black tree over bounded integer keys: the in-order walk equals sorted of the live keys after every op, and a shipped checker walking the tree verifies root black, no red father, and equal black height on every path, with remove of an absent key refused by name. | uv, python3 |
| `python-segment-tree` | A segment tree over an integer array with the combine as the seam: every window answer equals the matching slice sum exactly, a rebuild from the leaf row equals the build it came from, and no query visits more than twice the bit-length of the array. | uv, python3 |
| `python-fibonacci-heap` | A Fibonacci-ordered forest over integer-keyed items: the pop sequence equals sorted(corpus) on mixed push/pop/decrease storms, every degree stays under the log bound, and decrease-key never breaks heap order, checked by a shipped walk. | uv, python3 |
| `python-ring-buffer` | A fixed-capacity FIFO over integers: the drain equals the reference deque exactly under drop-oldest, the cursor never leaves [0, capacity), a full ring overwrites exactly the oldest, and the walk from (head, count) is the visible sequence after every op. | uv, python3 |
| `python-splay-tree` | A self-adjusting BST over integer keys: the walk equals sorted(live) on mixed insert storms, the touched key sits at the root after every access, and zig, zig-zig, and zig-zag preserve the in-order walk. | uv, python3 |
| `python-van-emde-tree` | A van Emde Boas tree over the fixed universe [0, 256): successor, predecessor, and membership equal the brute-force scans on seeded insert/delete/seek storms, the walk equals sorted(live) after every move, and empty-set seeks answer None, checked by a shipped audit. | uv, python3 |
| `python-kmp-automaton` | Knuth-Morris-Pratt over lowercase text: the scan's start list equals the naive scan's on seeded corpora, the failure table equals the naive border count, and overlaps and the empty pattern stay honest. | uv, python3 |
| `python-levenshtein` | Unit-cost edit distance over lowercase strings: the row walk equals a shipped exponential oracle on short pairs, reads the same from either side, never beats a detour, and nearest equals the scan's argmin with ties first by letters. | uv, python3 |
| `python-binary-heap` | A min-heap over integer keys, sift-up and sift-down hand-rolled on a plain list: the drain equals sorted(pushed) on seeded push/pop storms, and the parent rule is walked by a shipped checker after every op. | uv, python3 |
| `python-count-min` | A count-min sketch over [0, 256): the min of rows never dips under the ledger truth on seeded streams, the audit runs after every update, and the shipped grid answers its corpora exactly. | uv, python3 |
| `python-rabin-karp` | Rabin-Karp over lowercase text: the scan's start list equals the naive scan's on seeded corpora, the roll equals a fresh weigh on shipped windows, and collisions stay honest under a letter-check. | uv, python3 |
| `python-z-function` | The Z-array over lowercase words: the array equals the naive per-position LCP scan on seeded corpora, the concatenated occurrences equal the naive scan's starts, and z[0], the single letter, and the empty word stay honest. | uv, python3 |
| `python-bloom-filter` | A Bloom filter whose added keys are always answered present: the shipped audit re-asks every key after every update on seeded streams, the survey lists the liars at the shipped widths (none), and the rows are deterministic multiplicative hashes. | uv, python3 |
| `python-lz77` | LZ77 over lowercase text: the read hands back the letters the write was sent on shipped and seeded corpora, every back-reference names letters the window already emitted, and a repeat never costs more tokens than letters. | uv, python3 |
| `python-huffman-coding` | Canonical Huffman over lowercase text: decode(encode(text)) answers with the letters encode was sent on shipped and seeded corpora, no shipped code opens where another closes, and a skewed text pays strictly under eight bits a letter. | uv, python3 |
| `python-run-length` | Run-length over lowercase text: decode hands back the letters encode was sent on shipped and seeded corpora, encode answers exactly what the shipped stepper walks, and a repeat never costs more pairs than letters. | uv, python3 |
| `python-shunting-yard` | Infix to postfix and back: value_of answers exactly what the shipped recursive-descent oracle answers on shipped and seeded ledgers, and evaluate of the yielded queue equals the answer, division flooring as documented. | uv, python3 |
| `python-tarjan-scc` | Tarjan's strongly-connected components over small digraphs: the walker's partition equals the shipped reachability oracle's partition on every shipped and seeded corpus, every node lands in exactly one component, and the condensed graph is acyclic under the shipped cycle checker. | uv, python3 |
| `python-dijkstra` | single-source shortest paths over small nonneg-weight integer-keyed digraphs: the walker's distance map equals the shipped fixed-point oracle's map on every shipped and seeded corpus, every shipped path costs exactly the map's cost, and unreachable nodes stay out of the map. | uv, python3 |
| `python-bellman-ford` | Single-source shortest paths over small integer-weighted digraphs: the walker's distance map equals the shipped walk-counting oracle's map on every shipped and seeded corpus, no edge still relaxes after |V|-1 rounds, and negative cycles are named honestly. | uv, python3 |
| `python-prim-mst` | minimum spanning trees over small nonneg-weight undirected integer-keyed graphs: the grower's tree total equals the shipped enumeration oracle's minimum on every shipped and seeded corpus, every tree spans every node exactly once with |V|-1 edges, and equal weights pick the same edge set run after run. | uv, python3 |
| `python-topological-sort` | predecessors-first ordering of small integer-keyed digraphs: the order's listing validates against every shipped edge on every shipped and seeded corpus, every node sits exactly once, the sequence is a fixed point, and a cycle names its block honestly. | uv, python3 |
| `python-floyd-warshall` | all-pairs shortest paths over small nonneg-weight integer-keyed digraphs: the matrix's distance table equals the shipped walking oracle's table on every shipped and seeded corpus, the diagonal sits at zero, one more relaxation sweep changes nothing, and an unreached ordered pair stays omitted. | uv, python3 |
| `python-kruskal-mst` | minimum spanning trees over small nonneg-weight undirected integer-keyed graphs: the walker's tree total equals the shipped enumeration oracle's minimum on every shipped and seeded corpus, every tree spans every node exactly once with |V|-1 edges, the witness ledger tells the truth about every edge of the sorted list, and equal weights pick the same edge set run after run. | uv, python3 |
| `python-boruvka-mst` | minimum spanning trees over small nonneg-weight undirected integer-keyed graphs: the walker's tree total equals the shipped enumeration oracle's minimum on every shipped and seeded corpus, every tree spans every node exactly once with |V|-1 edges, every fragment reaches through its own cheapest edge each round, and equal weights pick the same edge set run after run. | uv, python3 |
| `python-counting-sort` | stable counting sort over small nonneg integer arrays: the sorted list equals the shipped oracle (sorted()) on every seeded corpus, equal keys keep their input order, the tally is the histogram, and the rank is its prefix; negative or oversized values are named, never sorted. | uv, python3 |
| `python-merge-sort` | stable merge sort over small nonneg integer arrays: the sorted list equals the shipped oracle (sorted()) on every seeded corpus, equal keys keep their input order, the middle splits the work and the merge walks both halves, and the rank is its prefix; negative or oversized values are named, never sorted. | uv, python3 |
| `python-quick-sort` | stable quick sort over small nonneg integer arrays: the sorted list equals the shipped oracle (sorted()) on every seeded corpus, equal keys keep their input order through a stable partition, the pivot partitions the array and each side sorts itself, and the rank is its prefix; negative or oversized values are named, never sorted. | uv, python3 |
| `python-heap-sort` | heap sort over small nonneg integer arrays: the sorted list equals the shipped oracle (sorted()) on every seeded corpus, the largest rides to the top and is peeled off last, and the rank is its prefix; negative or oversized values are named, never sorted. | uv, python3 |
| `python-insertion-sort` | insertion sort over small nonneg integer arrays: the sorted list equals the shipped oracle (sorted()) on every seeded corpus, the sorted prefix grows one value at a time walked leftwards, and the rank is its prefix; negative or oversized values are named, never sorted. | uv, python3 |
| `python-selection-sort` | selection sort over small nonneg integer arrays: the sorted list equals the shipped oracle (sorted()) on every seeded corpus, the smallest of the unsorted tail is chosen and swapped into place, and the rank is its prefix; negative or oversized values are named, never sorted. | uv, python3 |
| `python-bucket-sort` | bucket sort over small nonneg integer arrays: the sorted list equals the shipped oracle (sorted()) on every seeded corpus, the bucket index is value divided by the bucket width, and the rank is its prefix; negative or oversized values are named, never sorted. | uv, python3 |
| `python-radix-sort` | radix sort (LSD) over small nonneg integer arrays: the sorted list equals the shipped oracle (sorted()) on every seeded corpus, the digit is (value divided by ten to the power) mod ten, and the rank is its prefix; negative or oversized values are named, never sorted. | uv, python3 |
| `python-binary-search` | binary search over small sorted nonneg integer arrays: the index equals the shipped oracle (linear scan) on every seeded corpus, the middle is the pivot and the half that cannot hold the target is discarded, and a missing target answers -1; unsorted input is named, never searched. | uv, python3 |
| `python-linear-search` | linear search over small nonneg integer arrays: the first index equals the shipped oracle (first-match scan) on every seeded corpus, the first match wins and the walk stops there, and a missing target answers -1; out-of-range values are named, never searched. | uv, python3 |
| `python-gcd` | gcd (Euclid) and lcm over small positive integers: the result equals the shipped oracle (trial division) on every seeded pair, the remainder is taken until it vanishes, and coprime reports shared divisors; non-positive or oversized inputs are named, never divided. | uv, python3 |
| `python-sieve` | sieve of Eratosthenes up to small n: the prime list equals the shipped oracle (trial division) on every seeded n, each prime crosses off its multiples starting at its square, and is_prime agrees; non-positive or oversized n is named, never sieved. | uv, python3 |
| `python-factorial` | factorial and binomial over small n: n! equals the shipped oracle (sequential product) on every seeded n, the product grows by one factor at a time from 1 up to n, and binomial divides cleanly; negative or oversized n is named, never multiplied. | uv, python3 |
| `python-fibonacci` | fibonacci over small n: the n-th term equals the shipped oracle (recurrence) on every seeded n, each term is the sum of the two before it, and the list agrees; negative or oversized n is named, never computed. | uv, python3 |
| `python-palindrome` | palindrome check over small strings: is_palindrome agrees with the shipped oracle (reversal) on every seeded string, a string reads the same forwards and backwards, and reverse agrees; non-string or oversized input is named, never reversed. | uv, python3 |
| `python-anagram` | anagram check over small strings: is_anagram agrees with the shipped oracle (sorted comparison) on every seeded pair, two strings are anagrams when their sorted letters agree, and signature agrees; non-string or oversized input is named, never compared. | uv, python3 |
| `python-vowel-count` | vowel counting over small strings: count_vowels agrees with the shipped oracle (sum) on every seeded string, a vowel is one of a, e, i, o, u case-insensitively, and positions agree; non-string or oversized input is named, never counted. | uv, python3 |
| `python-digit-sum` | digit sum over small integers: digit_sum agrees with the shipped oracle (sum of decimal digits) on every seeded n, the product and count agree, and a negative or oversized n is named, never summed. | uv, python3 |
| `python-armstrong` | armstrong number over small integers: is_armstrong agrees with the shipped oracle (digit^count sum) on every seeded n, armstrong_sum agrees, and a negative or oversized n is named, never checked. | uv, python3 |
| `python-word-count` | word count over small strings: count_words agrees with the shipped oracle (split) on every seeded string, word_frequencies agrees, and a non-string or oversized input is named, never counted. | uv, python3 |
| `python-char-frequency` | character frequency over small strings: count_chars agrees with the shipped oracle (len) on every seeded string, char_frequencies agrees, and a non-string or oversized input is named, never counted. | uv, python3 |
| `python-prime-check` | prime check over small integers: is_prime agrees with the shipped oracle (trial division to sqrt) on every seeded n, prime_factors agrees, and a non-integer or oversized n is named, never checked. | uv, python3 |
| `python-lcm` | least common multiple over small integers: lcm agrees with the shipped oracle (a*b//gcd) on every seeded pair, gcd agrees, and a non-integer or oversized input is named, never divided. | uv, python3 |
| `python-gcd` | greatest common divisor over small integers: gcd agrees with the shipped oracle (Euclid) on every seeded pair, extended_gcd satisfies Bezout, and a non-integer or oversized input is named, never divided. | uv, python3 |
| `python-maximum-flow` | maximum flow over small nonneg-integer-capacity integer-keyed digraphs: the walker's value equals the brute-force min-cut oracle's least on every shipped and seeded corpus, the shipped map conserves at every interior node and never exceeds a capacity, and equal networks ship the same map run after run. | uv, python3 |
| `python-treap` | A binary search tree that is also a heap on seeded draws: insert, delete, rank, and select run through split and merge, heap and search order are re-checked after every mixed workload, and answers equal bisect's. | uv, python3 |
| `python-rope` | A binary rope of short leaf chunks with cached lengths: insert, delete, slice, and concat walk the spine instead of copying the text, and to_string is the join of the leaves in order. | uv, python3 |
| `python-graceful-shutdown` | A shutdown sequence you can deploy behind: in-flight requests finish before the process leaves, the listener closes so new clients are refused instead of queued, keep-alive requests get `503 draining` rather than being counted, a bounded drain exits 1 the moment the deadline is blown instead of joining the thread that blew it, a second signal exits 130, and `/health` flips to not-ready before any of it | `uv` |
| `python-c-extension` | A CPython extension built by setuptools and checked against its own pure-Python reference: `y*` takes any buffer (a `bytearray` is not read-only bytes), embedded NULs are ordinary bytes, and a test asserts the import really is the compiled `.so` rather than a fallback | `uv`, `gcc` |
| `python-smtp-sink` | A capturing SMTP server on aiosmtpd: each message is an `.eml` file plus one `fsync`ed index line, oversized mail is a `552`, a rejected recipient is a `550` with nothing stored, 8-bit headers need `enable_SMTPUTF8=True`, dot-stuffing is undone on the way in, and `rebuild` recreates the index from the files when the index is the thing that broke | `uv` |
| `python-resp-server` | A Redis-protocol (RESP2) server with a hand-written incremental parser: multibulk **and** inline grammars, pipelining, 100 KB binary values, lazy expiry against an injectable clock (so `TTL` is tested without sleeping), one lock so 100 concurrent `INCR`s are exactly 100, and one `-ERR Protocol error` followed by a close for a malformed frame. `redis-cli` is the client in the smoke test | `uv`, `redis-cli` |
| `python-dns-server` | An authoritative DNS server for one zone on UDP and TCP at the same time: the wire format is hand-written (compression pointers may only point backwards, names are capped at 255 bytes), a CNAME is emitted in the answer and then followed, an unknown name answers `NXDOMAIN` with the SOA in authority while a name outside the zone answers `REFUSED`, non-IN classes and non-QUERY opcodes answer `NOTIMP`, an EDNS0 payload size lets a 510-byte TXT through, and a datagram that still does not fit comes back with `TC` set and no records. `dig` is the client in the smoke test | `uv`, `dig` |
| `python-mqtt-broker` | An MQTT 3.1.1 broker with no dependencies: a hand-written remaining-length varint, CONNECT/PUBLISH/SUBSCRIBE with QoS 0 and 1, wildcard filters (`a/#` also matches `a`, `+` covers exactly one level), retained messages that are replayed **after** the SUBACK, clean sessions that forget everything while a persistent one keeps its filters, and one protocol error followed by a close for a wildcard publish topic. `mosquitto_pub`/`mosquitto_sub` are the clients in the smoke test | `uv`, `mosquitto-clients` |
| `python-websocket-server` | An RFC 6455 server on the standard library alone: the `Sec-WebSocket-Accept` handshake plus `404`/`400`/`426`/`405` rejections, a frame codec with 7/16/64-bit lengths, fragmentation reassembled before the app sees it, masking enforced in one direction only (server frames must **not** be masked), `1002`/`1003`/`1007`/`1009` for protocol mistakes, a close that echoes the peer's code, and a JSON `stats`/`echo`/`ping` protocol over the socket | `uv`, `curl` |
| `react-vite-ts` | React 19 + Vite + TS, Vitest + Testing Library, typecheck + build | `node`, `npm`/\`pnpm\`/\`yarn` |
| `vue-vite-ts` | Vue 3 + Vite + TS, Vitest + @vue/test-utils, typecheck + build | `node`, `npm`/\`pnpm\`/\`yarn` |
| `angular-app` | Angular 22 standalone component: `signal` + `computed` counters, Vitest with jsdom (no Karma, no Chrome), `ng build` bundle served by a zero-dependency static server with an SPA fallback, page/bundle/404 asserted by curl in `smoke.sh` | `node`, `npm`/`\`pnpm`\`/`\`yarn` |
| `nuxt-app` | Nuxt 4 SSR app over a shared counter: `pages/` for a real 404, one `server/api/stats.ts` for every method so `405` is the app's answer, Nitro `node-server` build, Vitest with no browser | `node`, `npm`/`\`pnpm`\`/\`yarn` |
| `next-app-ts` | Next.js App Router + TS + Tailwind 4, Vitest + Testing Library | `node`, `npm`/\`pnpm\`/\`yarn` |
| `chrome-extension` | MV3 extension: popup + service worker + content script, `npm run pack` → extension.zip | `node`, `npm`/\`pnpm\`/\`yarn` |
| `astro` | Astro + TS content site: typed frontmatter, Vitest unit tests, `astro check` + static build | `node`, `npm`/\`pnpm\`/\`yarn` |
| `ts-lib` | Publishable TS package: tsup ESM+CJS+`.d.ts`, split `exports` types per format, vitest, publint `--strict` and `npm pack --dry-run` gates | `node`, `npm`/\`pnpm\`/\`yarn` |
| `data-science` | pandas workspace: testable DataFrame helpers, pytest, sample notebook | `uv` |
| `sphinx-docs` | Sphinx site over a real package: autodoc, executed doctests, `-W` build, docs tested in CI | `uv` |
| `mkdocs-site` | MkDocs Material site whose Markdown examples are executed by a tested checker (`tools/check_fences.py`), `mkdocs build --strict` as the link gate | `uv` |
| `node-express-ts` | Express 5 API, typed handlers, supertest tests | `node`, `npm`/\`pnpm`/\`yarn` |
| `node-ws-api` | WebSocket service on bare Node: `ws` upgrade on one path only, presence broadcast on join/leave, count frames, live two-client contract test, SIGTERM drain | `node`, `npm`/\`pnpm`/\`yarn` |
| `node-upload-api` | Resumable uploads on bare Node: declared size, byte ranges at client-supplied offsets, `409 offset_mismatch` with the expected value, SHA-256 of the finished file, delete frees the bytes | `node`, `npm`/\`pnpm`/\`yarn` |
| `node-metrics-exporter` | Prometheus metrics from a hand-written registry: one HELP/TYPE per family, `_total` counters, cumulative buckets whose `+Inf` equals `_count`, labels on the matched route pattern (never the raw path), and a strict exposition reader the smoke test runs over the live payload | `node`, `npm`/`\`pnpm`/\`yarn` |
| `node-http2-api` | HTTP/2 with prior knowledge and no framework: raw `Http2Stream` handling on the `stream` event, `:path` query parsing, a body cap enforced while the stream is still arriving, concurrent-stream tests, and a curl contract that fails unless `%{http_version}` really is `2` | `node`, `npm`/`\`pnpm`/\`yarn` |
| `node-load-test` | HTTP load generator you can trust: latency measured from when a request was due (coordinated omission), warm-up excluded and counted, nearest-rank p50/p95/p99 named in the report, errorRate gated by default, and `replay` re-derives the summary from an archived sample file with no network | `node`, `npm`/`\`pnpm`/\`yarn` |
| `node-cli` | A text counter that is really about the command line: bytes taken from the buffer so a split UTF-8 character cannot corrupt the word count, the trailing word carried across chunks so a buffer boundary cannot split it, logical lines rather than `wc`'s newline count, `EPIPE` handled so `prog | head -1` exits 0 instead of printing a stack trace, unknown flags refused with exit 2, and `?` plus `ENOENT` instead of a zero for a file that could not be read | `node`, `npm` |
| `node-event-sourcing` | An append-only log whose guarantees are testable: every `append()` is one JSON line written with a single `writeSync` + `fsyncSync`, so a crash records a whole batch or none of it; a torn final line is dropped *and counted* while a torn line anywhere else raises, because guessing which records were lost invents history; `expectedVersion` makes two writers that both read "version 3" collide instead of last-write-wins, and the error names both numbers; versions are per stream and positions are global, so a checkpoint is one number rather than a tuple; a version hole refuses to load; and a projection must land on the same state whether rebuilt or resumed from `{position, state}`, which the CLI prints or exits non-zero on | `node`, `npm` |
| `node-stream-backpressure` | The same chunk series through the same slow sink four ways, with the buffer measured: ignoring a `write()` that returned false, `await Promise.resolve()` that is not backpressure, `drain` that is, and `pipeline()` that already does it — the peaks differ by 256x while the wall time does not, and the two transform mistakes that hang a process *without an error* are reproduced rather than described | `node`, `npm` |
| `node-worker-pool` | A fixed-size worker-thread pool whose contract is measured: workers are reused (64 tasks on 4 threads in 19 ms against 102 ms for 8 worker-per-task runs), the event loop keeps its timer ticking, `ArrayBuffer`s are *transferred* so the sender is detached, a full queue throws instead of growing, and a worker that dies rejects its task instead of leaving it hanging | `node`, `npm` |
| `node-http-cache` | Conditional requests you can watch. A real `node:http` server and a real client show the RFC 9110 rules and break them on purpose: `If-None-Match` compares weakly so a weak tag answers 304 while `If-Match` compares strongly so the same tag answers 412, a matching tag beats an old `If-Modified-Since`, a 304 carries zero bytes but must refresh freshness instead of emptying the stored body (the mistake is run on purpose and the entry is emptied for the rest of its window), `Vary: accept` proves the URL alone is not a cache key, and a 20-round run counts 323 of 340 bytes saved instead of estimating it. | node, npm, git |
| `hono-api` | Hono JSON API: `createApp()` returned as a value so tests use `app.request()` with no socket, `tsc` build (no bundler), `node dist/server.js` | `node`, `npm`/\`pnpm\`/\`yarn` |
| `fastify-api` | Fastify 5 API: the built-in JSON parser is removed so the raw body distinguishes `missing_text` from `invalid_json`, one catch-all route keeps the 404/405 table in a pure function, hand-serialised replies keep the key order | `node`, `npm`/`\`pnpm`/`\`yarn` |
| `prisma-api` | Prisma 6 over SQLite with Express 5: a readable initial migration replayed by `migrate deploy`, a `NoteStore` interface so the routes never import Prisma, `422`/`404`/`405` answers of the app's own, and a smoke test that restarts the server to prove the rows survive | `node`, `npm`/`\`pnpm`\`/\`yarn` |
| `openapi-spec` | OpenAPI 3.1 first: spectral lint with warnings as failures, redocly bundle + HTML reference, contract tests validating live responses against the bundle | `node`, `npm`/\`pnpm\`/\`yarn` |
| `graphql-api` | GraphQL Yoga with schema-first SDL: typed resolvers, a depth-limit plugin that answers `QUERY_TOO_DEEP` instead of hanging, `yoga.fetch()` tests with no socket, `tsc` build | `node`, `npm`/\`pnpm\`/\`yarn` |
| `playwright-e2e` | Browser-level suite: Playwright starts the fixture server itself (`webServer`, `reuseExistingServer: false`), chromium + a Pixel 7 project, `getByLabel` so an unassociated `<label>` fails, a horizontal-overflow check on mobile, traces kept on failure | `node`, `npm`/`\`pnpm`/`\`yarn` |
| `dbt-project` | Analytics engineering on dbt + DuckDB: seed → staging view → mart table, `+schema` per layer, generic + singular tests, `dbt build` runs models and tests, and a read-only script re-checks the numbers | `uv`, `git` |
| `nest-api` | NestJS 12 service: module/controller/service wiring, a validating pipe, supertest end-to-end tests, ESM throughout | `node`, `npm`/\\`pnpm\\`/\\`yarn` |
| `svelte-kit-ts` | SvelteKit + TS, Svelte 5 runes component, Vitest, static adapter build | `node`, `npm`/\`pnpm\`/\`yarn` |
| `github-action` | JavaScript action on `node24` (no Docker, zero deps): pure counting core, Markdown step summary, `GITHUB_OUTPUT` writes, `node:test` suite that spawns the real entry point | `node` |
| `go-cli` | stdlib-only Go CLI: `flag` parsing, table tests, vet/test/build gates | `go` |
| `go-http` | Go HTTP service on `net/http`: JSON routes, `httptest` suite, graceful shutdown | `go` |
| `grpc-go` | Protobuf-first Go service: `buf` lint/codegen, `bufconn` tests, real-socket smoke test, health service and reflection | `go` |
| `go-worker` | NDJSON batch worker: retries with backoff for retryable failures only, idempotency ledger written with temp file + rename, SIGTERM drain that does not wait for the producer | `go` |
| `go-jwt-api` | Go token service: PBKDF2 password digests, HMAC-signed bearer tokens with an absolute deadline, constant-time comparisons, an account store that writes atomically, and one indistinguishable 401 for expired-vs-forged | `go` |
| `go-trace-api` | W3C trace context without an SDK: a strict `traceparent` parser (lowercase hex, no all-zero ids, version `00`), an answer that names the span that served it, a child span linked to the request span, unsampled traces that propagate but store nothing, and a span export that is a ring reporting what it dropped | `go` |
| `go-tcp-framing` | Not HTTP at all: length-prefixed JSON frames over raw TCP, the frame cap checked *before* a buffer is allocated for it, a zero-length frame refused as a framing mistake, one goroutine per connection, an idle deadline so half-open clients cannot pile up, and a smoke test written against the byte format instead of a shared client library | `go`, `python3` |
| `go-wal-kv` | A write-ahead log behind a key/value API: every write is framed with a CRC32C length prefix and fsynced before the map changes, replay truncates a torn tail from the last segment, delete writes a tombstone, and compaction renames one fresh segment into place | `go`, `curl` |
| `go-consistent-hash` | Three in-process cache nodes behind a consistent-hash ring: 150 virtual nodes per node, an fmix64 finalizer over the FNV-1a digest (raw FNV-1a clusters sibling vnodes and hands one node 80% of the keys), replication to the first N owners, ring-order failover on read, and a rebalance that moves only the victim's keys | `go`, `curl` |
| `rust-cli` | std-only Rust CLI: lib+bin split, fmt/clippy/test/release-build gates | `cargo` |
| `rust-axum` | axum service: typed routes, shared state, `tower` oneshot tests, fmt/clippy | `cargo` |
| `actix-web` | actix-web 4 service with hand-owned routing: an any-method route so the `405`/`404` bodies are JSON of the app's own, a struct (not `json!`) so the key order is byte-exact, a percent decoder that returns bytes, 39 offline self-checks plus a live curl contract that reaps its own server | `cargo`, `git` |
| `rust-sqlx-api` | notes API on axum + sqlx/SQLite: migrations embedded in the binary, `rows_affected() == 0` as the only honest 404, struct-ordered JSON, four integration tests against a real database file, 41 offline self-checks plus a live curl contract | `cargo`, `git` |
| `c-cli` | C11 CLI: Makefile lib+bin split, assert-header test suite, `-Wall -Wextra -Wpedantic -Werror` from the first commit | `cc`, `make` |
| `c-http-api` | C11 JSON service on POSIX sockets: pure `textstat_route`, a hand-written JSON reader that keeps strings and numbers apart, and a socket loop with 5 s read timeouts | `cc`, `make` |
| `cpp-cmake-cli` | C++20 CLI: CMake lib+bin split, CTest suite, warning-clean GCC/Clang build | `cmake`, `g++` |
| `cpp-http-api` | C++17 JSON service with a plain Makefile and POSIX sockets: a validating JSON reader that keeps a number apart from a string, pure `route`, hand-rolled check harness | `c++`, `make` |
| `terraform-module` | Reusable module: validated inputs, computed tags, `terraform test` cases incl. a rejected input | `terraform` |
| `ansible-role` | Galaxy-shaped Ansible role: validated inputs, idempotent tasks, a handler, molecule-free playbook + assert playbooks | `ansible-playbook` |
| `ruby-sinatra` | Sinatra JSON API: modular app, RSpec + rack-test suite, RuboCop, committed lockfile | `ruby`, `bundle` |
| `rails-app` | Rails 8 JSON app: a service object for the counting, an integration test that goes through the router, SQLite, committed lockfile | `ruby`, `bundle` |
| `ruby-cli` | Ruby CLI in gem shape: `Data` value objects, injected I/O, minitest suite via `rake`, no gems to install | `ruby`, `rake` |
| `java-maven-cli` | Java 21 CLI on Maven: pure counting logic, 21 JUnit 5 tests, runnable jar | `java`, `mvn` |
| `spring-boot` | Java 21 Spring Boot 3 web service on Maven: a wc-style `/stats` endpoint, a pure service, and a JUnit 5 + MockMvc suite | `java`, `mvn` |
| `java-httpserver-api` | Java 21 JSON service on the JDK's own `com.sun.net.httpserver`: counting and contract classes with no framework, a hand-written JSON reader, and a Makefile over `javac -Xlint:all -Werror` | `java`, `make` |
| `php-composer-cli` | PHP 8.3 CLI on Composer: PSR-4 autoloading, a PHPUnit 11 suite, and a wc-style text counter | `php`, `composer` |
| `symfony-app` | Symfony 7 web app on PHP 8.3: a JSON route wired to a pure service, kernel-level PHPUnit test, working `bin/console` | `php`, `composer` |
| `laravel-app` | Laravel 13 JSON service on PHP 8.3: pure counting class, route + controller, PHPUnit 12 suite covering 422/404 and the input-trimming trap | `php`, `composer` |
| `csharp-cli` | C# 12 CLI on .NET 8: pure counting library, xUnit suite, exit codes as a contract | `dotnet` |
| `aspnet-api` | ASP.NET Core 8 minimal API: pure counting core, `/stats` JSON routes, WebApplicationFactory HTTP tests, 422/404 as contract | `dotnet` |
| `dotnet-cli` | .NET 8 C# CLI with a solution file: counting core, hand-written argv parser, xUnit suite, exit codes as a contract | `dotnet` |
| `elixir-mix-cli` | Elixir CLI on Mix: pure counting module, ExUnit suite, escript binary | `elixir`, `mix` |
| `phoenix-app` | Phoenix 1.8 JSON API on Elixir 1.18: pure counting module, endpoint + router + controller, ConnTest suite covering 422/404, `mix format` gate | `elixir`, `mix` |
| `dart-cli` | Dart 3 CLI: pub package with a pure counting library, package:test suite and zero runtime dependencies | `dart` |
| `dart-shelf-api` | Dart 3 JSON service on `shelf`: a `Handler` the tests call in-process, `shelf_router` routes, real-socket smoke test | `dart` |
| `kotlin-cli` | Kotlin CLI on Maven (no Gradle wrapper to ship): pure counting core, JUnit 5 suite, shaded runnable jar | `java`, `mvn` |
| `kotlin-http-api` | Kotlin JSON service on the JDK `HttpServer`: the counting core and router are pure Kotlin, `--selftest` replaces the test runner, one shaded jar to run | `java`, `mvn`, `curl` |
| `kotlin-ktor-api` | Ktor 3 service on JDK 21: raw `Application` interception instead of routing so 404/405 bodies stay byte-exact, a hand-rolled strict JSON scanner (kotlinx accepts `"text":42`), a Maven Kotlin build that wires the serialization compiler plugin, and a shaded jar that keeps the engine's `META-INF/services` | `java`, `mvn`, `curl` |
| `zig-cli` | Zig 0.17 CLI: counting module with in-source test blocks, `zig build test`, no runtime | `zig` |
| `zig-http-api` | Zig 0.17 JSON service on `std.http`: `contract.route` is pure so every status code is tested without a socket, `build.zig` ships the binary plus one test binary per module, real-socket verify step | `zig`, `curl` |
| `julia-cli` | Julia CLI: pure counting module, `Test` stdlib suite, zero external packages | `julia` |
| `julia-api` | Julia JSON service on HTTP.jl: pure `route(method, path, query, body)`, `Test` suite covering every status code plus one real-port case, 18-package instantiate once | `julia`, `curl` |
| `nim-cli` | Nim CLI: pure counting module, `unittest` suite that also checks exit codes, `nimble build` binary | `nim`, `nimble` |
| `nim-http-api` | Nim JSON service: counting core, a pure `route()` covering every status code, `asynchttpserver` on top — no dependencies at all | `nim`, `nimble` |
| `perl-cli` | Perl CLI on core modules only: `Makefile.PL` + `Test::More` suite, no CPAN install step | `perl`, `make` |
| `perl-mojolicious-api` | Mojolicious JSON service on Perl 5: a pure `Textstat::Contract->route(method, path, query, body)` covering every status code, a `Test::More` suite, and a numeric-vs-string check that survives `JSON::PP` | `perl`, `make`, `Mojolicious` |
| `lua-cli` | Lua 5.4 CLI: stdlib-only modules, a hand-rolled spec harness, zero luarocks dependencies | `lua5.4` |
| `lua-http-api` | JSON service on LuaSocket: the route table as one pure function, JSON written by hand so the key order is stable, a framework-free suite, one script binds the socket | `lua5.4`, `lua-socket`, `lua-cjson` |
| `fsharp-cli` | F# on .NET 8: pure counting core, `Mode` discriminated union parser, xUnit suite that launches the binary for its exit codes | `dotnet` |
| `fsharp-http-api` | F# JSON service on .NET 8 with no web framework: a byte-level `TcpListener` loop, a hand-written JSON reader that re-encodes escapes, and a `--selftest` mode with 34 checks | `dotnet`, `curl` |
| `crystal-cli` | Crystal CLI: stdlib-only modules, `crystal spec` suite, compiled binary with a 0/2/1 exit contract | `crystal` |
| `crystal-kemal-api` | Crystal service on Kemal: counting rules and the whole route table are pure functions under `crystal spec`, plus a real socket check | `crystal`, `shards` |
| `bun-cli` | Bun CLI: pure counting module, hand-written option parser, zero-dependency `bun:test` suite | `bun` |
| `bun-api` | Bun JSON service: one `Request`→`Response` handler, `Bun.serve`, `bun:test` suites, `tsc --noEmit` via `bun run typecheck`, real socket smoke test | `bun` |
| `bun-sqlite-api` | Bun with zero dependencies: `Bun.serve` routes, `bun:sqlite` with per-connection PRAGMAs read back through `query` (not `exec`), numbered migrations inside `db.transaction()`, `bun:test` over a real port, and a restart that proves the rows are in the file, not in the process | `bun` |
| `r-cli` | R CLI on base R only: pure counting function, hand-written option parser, dependency-free test harness | `Rscript` |
| `r-plumber-api` | Plumber JSON service in R: annotated routes, a pure `textstat_route(method, path, query, body)` covering every status code, a base-R test harness, and a JSON 404 built into `bin/serve.R` | `Rscript`, `plumber` |
| `ocaml-cli` | OCaml CLI on dune: pure counting library, hand-written option parser, stdlib-only test harness, zero opam dependencies | `ocaml`, `dune` |
| `ocaml-http-api` | OCaml JSON service on the `Unix` module: pure `route`, a hand-written JSON reader that keeps `42` apart from `"42"`, and three `dune runtest` suites over a stdlib harness | `ocaml`, `dune` |
| `static-site` | HTML/CSS/JS page, `node:test` suite, GitHub Pages deploy workflow | `node` |
| `hugo-site` | Content site on Hugo: hand-written layouts and partials, a shortcode, fingerprinted CSS, sitemap and RSS, assertion suite that renders into a temp dir | `hugo` |
| `helm-chart` | Kubernetes Helm chart: schema-validated values, named templates, hardened Deployment/Service, lint+render checks with no cluster | `helm` |
| `gleam-cli` | Gleam CLI: pure counting module, hand-written option parser, stdlib-only test harness, Erlang helper for argv/stdin/exit codes | `gleam` |
| `gleam-mist-api` | Gleam JSON service on Mist: pure request contract, gleeunit suite, counted over a real socket | `gleam`, `rebar3` |
| `scala-cli` | Scala 3 CLI built with scala-cli (no sbt): pure counting core, hand-rolled argv parser, munit suites, wrapper that returns the process exit code | `scala-cli`, `java` |
| `scala-cask-api` | Scala 3 JSON service on Cask: pure request contract, utest suite, one assembly jar served over a real socket | `scala-cli`, `java` |
| `haskell-cli` | Haskell CLI on GHC and cabal: pure counting core, hand-rolled argv parser, dependency-free test harness, I/O behind a record | `ghc`, `cabal` |
| `haskell-warp-api` | Warp JSON service on GHC: `Contract.route` is pure so every status code is testable without a socket, a hand-written JSON reader keeps the dependency set to warp/wai, and a plain exitcode-stdio suite gates it | `ghc`, `cabal` |
| `clojure-cli` | Clojure CLI on `deps.edn` (no Leiningen): pure counting core, hand-rolled argv parser, `clojure.test` suites, I/O behind a record | `clojure`, `java` |
| `clojure-ring-api` | Ring JSON service on `deps.edn`: the handler is a plain request-map function, `ring.mock` drives the routes with no port, Jetty serves it, `clojure.test` gates it | `clojure`, `java` |
| `swift-cli` | Swift 6 CLI on SwiftPM: pure counting core, hand-rolled argv parser, XCTest suites, I/O behind a struct of closures | `swift` |
| `swift-http-api` | Swift 6 JSON service on raw POSIX sockets with `swiftc` instead of a package manifest: pure counting and contract types, a hand-written JSON reader, 34 checks run by `--selftest` | `swift`, `make` |
| `tcl-cli` | Tcl CLI on plain `tclsh`: byte-level counting core, hand-rolled argv parser, dependency-free test harness, I/O behind a dictionary | `tclsh` |
| `tcl-http-api` | Tcl JSON service on plain `tclsh`: a hand-written strict JSON reader (no tcllib), the route table as one pure function, and a socket server that binds in one file | `tclsh` |
| `erlang-cli` | Erlang CLI on plain OTP and `make`: byte-level counting core, hand-rolled argv parser, eunit suites, I/O behind a map of funs | `erl`, `erlc`, `make` |
| `erlang-cowboy-api` | Erlang JSON service on Cowboy: pure `route(Method, Path, Query, Body)` covering every status code, eunit suites, an escript release, and a real-socket verify step | `erl`, `rebar3` |
| `racket-cli` | Racket CLI on the core distribution: byte-counting core, struct-based argv parser, `rackunit` suites, I/O behind a struct of funs | `racket`, `raco` |
| `racket-api` | Racket JSON service on the built-in web server: the route table is one pure function, `rackunit` tests with no socket, and a single file binds the port | `racket`, `raco` |
| `deno-cli` | TypeScript CLI on Deno: byte-counting core, pure argv parser, `Deno.test` suites, I/O behind an object of functions | `deno` |
| `deno-api` | Deno 2 JSON service: one `Request`→`Response` handler, `Deno.serve`, std assertions, check/fmt/lint gates and a real socket smoke test | `deno` |
| `vhdl-sim` | VHDL design with a self-checking testbench on GHDL: one clocked process, assertion-driven simulation, a run script that fails CI on a wrong design | `ghdl` |
| `fortran-cli` | Fortran CLI on `gfortran` and `make`: byte-exact counting core, hand-rolled argv parser, dependency-free test harness, output units injected | `gfortran`, `make` |
| `fortran-http-api` | Fortran JSON service on `gfortran`: libc sockets through `ISO_C_BINDING`, a hand-written JSON reader over `int8` bytes, and a dependency-free `--selftest` mode | `gfortran`, `make`, `curl` |
| `ada-cli` | Ada CLI on GNAT: byte-exact counting core, hand-rolled argv parser, dependency-free test harness, output through two subprogram parameters | `gnatmake`, `make` |
| `ada-http-api` | Ada JSON service on `GNAT.Sockets`: pure counting and contract packages, one pure `Route (method, path, query, body)` covering every status code, and a validating JSON reader that keeps a number apart from a string | `gnatmake`, `make` |
| `octave-cli` | Octave CLI on plain `octave`: counting core in a `+textstat` package, hand-rolled argv parser, dependency-free suite, environment injected as function handles | `octave` |
| `octave-http-api` | Octave JSON service on the bundled JVM bridge: `java.net.ServerSocket`, a hand-written JSON reader over `uint8` bytes, and a framework-free self test | `octave`, `curl` |
| `prolog-cli` | SWI-Prolog CLI: byte-exact counting over a stream, hand-rolled argv parser, a four-predicate test harness, output behind two writer closures | `swipl` |
| `prolog-http-api` | SWI-Prolog JSON service on `library(http/http_server)`: the route table is one pure predicate, a plain Prolog script tests it, one module binds the port | `swipl` |
| `lisp-cli` | Common Lisp CLI on SBCL: byte-exact counting core, hand-rolled argv parser, dependency-free test harness, I/O through a structure of functions | `sbcl` |
| `lisp-http-api` | Common Lisp JSON service on SBCL: pure `route` function, a hand-written JSON reader that keeps strings and numbers apart, and an HTTP loop on `sb-bsd-sockets` | `sbcl` |
| `pascal-cli` | Free Pascal CLI on FPC and `make`: byte-exact counting unit, hand-written argv parser, dependency-free test suite, terminal behind a record of function pointers | `fpc`, `make` |
| `pascal-http-api` | Free Pascal JSON service on the fcl-web listener: pure counting and contract units, one pure `Route(method, path, query, body)` covering every status code, and a JSON reader that decodes `\u` escapes into UTF-8 itself | `fpc`, `make`, `fp-units-fcl` |
| `bash-cli` | Bash CLI on plain `bash` and `shellcheck`: counting in bash itself (no `wc`, no `awk`), hand-rolled argv parser, dependency-free test harness, terminal behind sourced functions | `bash`, `shellcheck` |
| `cobol-cli` | COBOL CLI on GNUCOBOL: byte-exact counting over a one-byte sequential read, hand-rolled argv parser reading `/proc/self/cmdline`, a COBOL unit driver plus a shell suite, I/O in one program | `cobc`, `make` |
| `guile-cli` | Scheme CLI on GNU Guile: bytevector counting core, hand-rolled argv parser, dependency-free harness, ports behind a record of procedures | `guile` |
| `guile-http-api` | Guile JSON service on the built-in web server: counting over the UTF-8 bytes, the route table as one pure procedure, a framework-free test suite, one script binds the socket | `guile`, `guile-json` |
| `raku-cli` | Raku CLI on Rakudo: `Buf` counting core, hand-rolled argv parser, dependency-free harness, the four side effects handed in as closures | `raku` |
| `raku-http-api` | Raku JSON service on Rakudo's own `IO::Socket::INET`: a `Buf` counting core, a hand-written JSON reader (no `JSON::Fast`, no `zef`), and the route contract tested without a socket | `raku`, `curl` |
| `groovy-cli` | Groovy CLI on the plain Groovy runtime: byte-array counting core, hand-rolled argv parser, dependency-free harness, the four side effects handed in as closures | `groovy`, `java` |
| `groovy-http-api` | Groovy JSON service on the JDK's `com.sun.net.httpserver`: pure `route`, `JsonSlurper` keeping a number apart from a string, and a plain-script test gate — no Gradle, no JUnit | `groovy` |
| `awk-cli` | awk CLI on `gawk`: counting with `RS="\0"` so each file is one record, hand-rolled argv parser, dependency-free harness, the report built before anything is printed | `gawk` |
| `forth-cli` | Forth CLI on `gforth`: counting over a memory block with a loop and `c@`, hand-rolled argv parser, a four-word test harness, terminal reads behind one file | `gforth` |
| `sqlite-sql` | SQL reporting project on SQLite: schema with `CHECK` constraints, views that hold the arithmetic, one `SELECT` per report, assertions over exact cents | `sqlite3`, `make` |
| `jq-report` | Reports over a JSON access log as plain jq programs: status counts, busiest paths, slowest requests, bytes per day, error rate, behind a shell command with a tested exit-code contract | `jq`, `make` |
| `powershell-cli` | PowerShell 7 CLI: byte loop over the payload, hand-rolled argv parser, I/O behind a hashtable of scriptblocks, a harness with no gallery modules | `pwsh` |
| `powershell-api` | PowerShell 7 JSON service on `HttpListener`: counting and the route table in a module, a framework-free test script, one script binds the socket | `pwsh` |
| `docker-compose-svc` | A small HTTP service shipped as a container: non-root image with a real HEALTHCHECK, compose file driven by `PORT`, pure-function contract with unit tests that need no Docker, and a smoke test that starts the container, checks every answer and leaves nothing running | `docker`, `make` |
| `jsonnet-config` | A service manifest in Jsonnet with its rules as data: validators that name every problem, a renderer that sorts and sums, and an 18-check suite that proves each rule fires | `jsonnet`, `make` |
| `d-cli` | D compiled with LDC: counting over `ubyte[]`, hand-written argv parser, report building behind an `Io` struct of function pointers, a 37-assertion harness and a parity suite that diffs the output against `wc` | `ldc2`, `make` |
| `d-http-api` | D JSON service on `std.socket`: pure `route`, `std.json` for the body, one request per connection, and the total absence of a test framework — the tests are `unittest` blocks | `ldc2`, `make` |
| `sml-cli` | Standard ML compiled with MLton to a single native binary: counting over `Word8Vector`, hand-written argv parser, a 37-assertion SML harness and a parity suite that diffs the output against `wc` | `mlton`, `make` |
| `sml-http-api` | Standard ML JSON service on `INetSock.TCP`: counting over `Word8Vector`, a hand-written JSON reader with surrogate pairs and a router tested without a socket, all compiled by MLton | `mlton`, `make`, `curl` |
| `haxe-cli` | Haxe command line tool compiled to Neko: byte-accurate `wc`-style counting, hand-written option parser, dependency-free Haxe test suite plus a parity suite that diffs the output against `wc` | `haxe`, `neko`, `make` |
| `haxe-http-api` | Haxe JSON service on the eval target: no build step, a hand-written JSON reader that keeps a number apart from a string, and a blocking `sys.net.Socket` loop that waits for the client to hang up so the port is free for the next run | `haxe` |
| `mdbook-docs` | An mdBook site with a shell link checker wired into CI: relative links and images must exist, every page must be listed in `src/SUMMARY.md`, and 25 assertions prove it catches broken links, missing images and orphan pages | `mdbook`, `make` |
| `latex-paper` | A two-page LaTeX article with a real bibliography, gated on the PDF a reader gets: `latexmk` plus `bibtex`, then `pdftotext` assertions for the title, the headings, the `[1]` citation and the page count, and the build log itself inspected for overfull lines and unresolved references | `latexmk`, `pdflatex`, `pdftotext`, `make` |

Each generated project ships its own `.github/workflows/` that is ready to run, plus a
README, a licence (`--license mit|apache-2.0|bsd-3|none`), a version floor for the Python
and JavaScript stacks (`--python 3.13`, `--node 24`), the package manager a
JavaScript stack's commands are written for (`--package-manager pnpm`), a
`.gitignore`, and a
`.newstack.json` record that `newstack update` uses to re-apply later template changes.

## Adopting an existing project

Most projects do not start from a scaffold. `adopt` retrofits a stack's *infrastructure*
onto a directory that already has code — and it is additive by construction: **an existing
file is never opened for writing.**

```console
$ newstack adopt ~/sites/analytics-dashboard
newstack 0.3.0  ·  adopt  →  /home/you/sites/analytics-dashboard

  stack        static-site (auto-detected)
  added        2 files
      + .github/workflows/deploy-pages.yml
      + .gitignore
  tests        not copied — rerun with --with-tests if you want starter tests
```

- **Detection** reads the project's own markers (`go.mod`, `Cargo.toml`, `manage.py`, the
  dependencies in `pyproject.toml` / `package.json`, a bare `index.html`). If two stacks
  match, it prints the candidates and exits 2 rather than guessing; `--stack` overrides.
- **Scope**: workflows, `.gitignore`, and per-stack lint/type config only. It will not copy
  a README, a LICENSE, a `pyproject.toml`, or source files — those carry your project's
  identity, not infrastructure.
- **Merges are reported, not attempted.** If your `pyproject.toml` needs the stack's
  `[tool.ruff]` block, adopt says so and leaves the file alone.
- `--dry-run` prints the same report without writing. Re-running is a no-op.
- `--with-tests` additionally copies the stack's *starter* tests — experimental, because
  those tests import the sample module and usually need adapting to your code.

## Keeping a project current

`newstack new` leaves a `.newstack.json` record in the project: the render context plus a
sha256 for every file it wrote. `update` re-renders the *current* template with that
recorded context — so the project keeps its own name, author and dates — then compares
three things per file: what newstack wrote, what is on disk now, and what the template
ships today.

```console
$ newstack update ~/code/tool
newstack 0.4.0  ·  update python-cli  →  /home/you/code/tool

  stack         python-cli (.newstack.json, generated by newstack 0.4.0)
  wrote         1 file
      ~ .gitignore
  conflict      1 file differs — left untouched
      ! README.md
        locally edited; --force takes the template's version
  unchanged     8 files

  keep your edits, or take the template's:
    git -C /home/you/code/tool diff --stat
    newstack update /home/you/code/tool --force
  record        .newstack.json updated (newstack 0.4.0)
```

- **Untouched files are refreshed.** A file that still matches what newstack wrote takes
  the template's new version — that is the whole point of updating.
- **Edited files are conflicts, not overwrites.** They are reported, skipped, and the run
  exits 1. The record keeps the hash newstack last wrote, so your edit stays a conflict on
  every later run instead of being mistaken for upstream and quietly replaced;
  `--force` takes the template's version when you have decided you do not want yours.
- **Added files arrive; dropped files are reported.** Files the template no longer ships
  are only deleted with `--prune`, and only while they still equal what newstack wrote —
  `update` will not eat a file you have edited.
- **Projects without a record still work.** `update --stack python-cli` renders with the
  directory name, and treats every existing file it did not write as a conflict.
- `--dry-run` prints the same plan and writes nothing; `--json` is there for scripts.
- **`outdated` is the read-only half.** It never writes, so it is safe in a CI job or a
  pre-commit hook: exit 0 when the project matches the template, 1 when there is
  something to pull — or when there is no record to compare against.

```console
$ newstack outdated ~/code/tool
newstack 0.4.0  ·  outdated python-cli  →  /home/you/code/tool

  stack         python-cli (.newstack.json, generated by newstack 0.4.0)
  behind        1 file newer in the template
      ~ .gitignore
  missing       1 file the template adds
      + docs/guide.md
  modified      1 file you edited — update will conflict
      ! src/tool/__init__.py

  newstack update /home/you/code/tool
```

## The green guarantee

A template is only as good as its last successful run, so `newstack` treats
verification as a first-class command:

```console
$ newstack check --all
  django           PASS    1.5s  5 step(s)
  fastapi          PASS    1.4s  3 step(s)
  go-cli           PASS    0.3s  3 step(s)
  node-express-ts  PASS    6.1s  3 step(s)
  python-cli       PASS    0.5s  4 step(s)
  python-lib       PASS    0.5s  3 step(s)
  react-vite-ts    PASS    5.5s  4 step(s)
  rust-cli         PASS    0.5s  4 step(s)
  static-site      PASS    0.1s  3 step(s)
  svelte-kit-ts    PASS    7.1s  4 step(s)
```

(Real timings from a warm package cache — a cold run takes about a minute because
`npm install` and `uv pip install` have to fetch packages.)

`check` generates the stack into a throwaway directory, runs the commands listed in its
manifest (`install → lint → test → build`), reports per-step timings, and deletes the
directory unless you pass `--keep`. The same command runs in this repository's CI, once
per stack, on every push.

## How it compares

| | newstack | cookiecutter | copier | yeoman | degit / `npm create` | `gh repo create --template` |
| --- | --- | --- | --- | --- | --- | --- |
| Cross-language stacks in one tool | **yes** | no | no | partial | no | n/a |
| Runtime dependencies | **0** | Python | Python + git | Node | Node | gh |
| Generated starter verified in CI | **yes, per stack** | no | no | no | no | no |
| Template updates after generation | **yes** (`update`, keeps your edits) | no | **yes** (`copier update`) | no | no | no |
| Creates the git repo + remote | **yes** (`--github`) | no | via hooks | no | no | yes |

Pick `copier` when you want one long-lived Jinja template with hooks and a `copier update`
flow. Pick `newstack` when you want the same standard applied across several languages
without maintaining one template per stack — `newstack update` gives you the same
three-way merge, with no templating language to learn.

## Adding a stack

A stack is a directory with a manifest and a template tree. The manifest carries four
optional keys beyond the basics — `detect` (how a directory is recognised as this stack),
`detect_fallback` (a generic stack that must lose to a specific match), and the `adopt` /
`adopt_tests` allow-lists used by `newstack adopt`:

```text
src/newstack/data/stacks/my-stack/
├── stack.json
└── template/
    ├── README.md
    └── ...                      # {{ project_name }}, {{ package_name }}, {{ npm_name }},
                                 # {{ title }}, {{ description }}, {{ author }}, {{ email }},
                                 # {{ year }}, {{ date }}
```

```json
{
  "name": "my-stack",
  "title": "My stack",
  "language": "python",
  "blurb": "One line shown by `newstack list`",
  "requires": ["uv"],
  "next_steps": ["cd {path}", "uv run pytest"],
  "verify": [
    {"name": "test", "cmd": "uv run pytest", "tools": ["uv"], "timeout": 600}
  ],
  "detect": [{"file": "pyproject.toml", "contains": "my-framework"}],
  "adopt": [".github/workflows/ci.yml", ".gitignore"],
  "adopt_tests": ["tests/test_smoke.py"]
}
```

`adopt` entries must exist in the template and must never be an identity file
(`README.md`, `LICENSE`, `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`) — a
test enforces both rules.<br>
`{{!` escapes a literal `{{`, and `${{ ... }}` (GitHub Actions) is left untouched.
Point `NEWSTACK_STACKS` at a directory of your own stacks to use private ones — same
manifest format, no fork required.

## Design

- **Zero runtime dependencies.** `argparse` and the standard library only, so `uvx newstack`
  starts instantly and works offline.
- **Templates are plain files.** No Jinja, no DSL — a reviewer can read a template and know
  exactly what gets written.
- **Verification is a product feature, not an afterthought.** `check` is the same code path
  CI uses.
- **A licence is data, not a template detail.** One copy of each licence text lives in
  `data/licenses/`, so 46 templates cannot drift apart and `--license none` is a real
  choice rather than a deleted file.
- **A version is written once.** `--python` fills `requires-python`, the ruff target, the
  classifiers, the CI matrix and the Docker tag; `--node` fills `engines` and the JS CI
  matrix; `--package-manager` fills every install/test/run command, the lockfile name and
  the step that installs the manager itself. One value per decision, so a project cannot
  claim support for a version its own CI never runs, or carry an `npm` command in a `pnpm`
  workflow.
- **Updates are a hash comparison, not a diff dance.** `.newstack.json` records what
  newstack wrote; a file counts as yours only once it stops matching that hash, so
  `update` never has to guess whose change it is looking at.
- **A stack you install is labelled as one.** `stacks add` validates everything before it
  writes anything, and every command that follows says `[installed]`, because "this
  repository's CI proved it" is a smaller claim than "someone published it".

## Roadmap

- More stacks once the toolchains are available here: Groovy/Gradle, Nix.

  Open an issue with the stack or flag you want next.

## Licence

MIT — see [LICENSE](LICENSE).
