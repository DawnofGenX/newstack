# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-11-16

280 new starter stacks since 0.4.0, across 58 languages. Every stack is
generated and verified on a clean runner; the stack matrix is now sharded so that growth
past GitHub's 256-job matrix cap cannot silently stop that verification (docs/CI.md).

### Added

#### Stacks

- **Python (163)**: `dbt-project`, `mkdocs-site`, `python-ab-test`, `python-aho-corasick`,
  `python-anagram`, `python-armstrong`, `python-audit-log`, `python-avl-tree`, `python-b-tree`,
  `python-backoff-jitter`, `python-batch-inference`, `python-bellman-ford`,
  `python-binary-heap`, `python-binary-search`, `python-binomial-heap`, `python-bk-tree`,
  `python-bloom-filter`, `python-boruvka-mst`, `python-bracket-matching`, `python-bubble-sort`,
  `python-bucket-sort`, `python-c-extension`, `python-caesar-cipher`, `python-char-frequency`,
  `python-circuit-breaker`, `python-cocktail-sort`, `python-coin-change`, `python-comb-sort`,
  `python-combinations`, `python-config-precedence`, `python-consistent-hashing`,
  `python-count-min`, `python-count-min-sketch`, `python-counter-rollup`,
  `python-counting-sort`, `python-crdt`, `python-cron-schedule`, `python-cycle-sort`,
  `python-decimal-to-binary`, `python-dependency-resolver`, `python-deque`, `python-digit-sum`,
  `python-dijkstra`, `python-dns-server`, `python-duckdb-report`, `python-eval-harness`,
  `python-expression-parser`, `python-factorial`, `python-fastapi-sqlite`,
  `python-feature-flags`, `python-fenwick-tree`, `python-fibonacci`, `python-fibonacci-heap`,
  `python-floyd-warshall`, `python-gcd`, `python-gitignore-matcher`, `python-gnome-sort`,
  `python-graceful-shutdown`, `python-hamming-distance`, `python-hdr-histogram`,
  `python-heap-sort`, `python-html-sanitizer`, `python-huffman-coding`, `python-hybrid-clock`,
  `python-hyperloglog`, `python-idempotency-keys`, `python-insertion-sort`,
  `python-interpolation-search`, `python-interval-tree`, `python-intro-sort`,
  `python-json-patch`, `python-kd-tree`, `python-keyset-pagination`, `python-kmp-automaton`,
  `python-knapsack`, `python-kruskal-mst`, `python-lcm`, `python-lcs`, `python-leases-fences`,
  `python-levenshtein`, `python-linear-search`, `python-linearizability-checker`, `python-lis`,
  `python-litestar-api`, `python-longest-common-substring`, `python-lru-cache`,
  `python-lsm-tree`, `python-lz77`, `python-max-subarray`, `python-maximum-flow`,
  `python-merge-sort`, `python-merkle-proofs`, `python-migrations`, `python-minhash-lsh`,
  `python-money-allocation`, `python-monotonic-stack`, `python-mqtt-broker`,
  `python-odd-even-sort`, `python-openapi-client`, `python-outbox-pattern`, `python-palindrome`,
  `python-pancake-sort`, `python-pdf-report`, `python-permission-model`, `python-permutations`,
  `python-power`, `python-prefix-trie`, `python-prim-mst`, `python-prime-check`,
  `python-property-tests`, `python-pytest-plugin`, `python-quick-sort`, `python-rabin-karp`,
  `python-radix-heap`, `python-radix-sort`, `python-rag-eval`, `python-rate-limiter`,
  `python-red-black-tree`, `python-regex-engine`, `python-resp-server`, `python-retry-budget`,
  `python-ring-buffer`, `python-roman-numerals`, `python-rope`, `python-route-trie`,
  `python-rrule-recurrence`, `python-run-length`, `python-saga-compensation`,
  `python-scapegoat-tree`, `python-scheduler-api`, `python-schema-evolution`,
  `python-segment-tree`, `python-selection-sort`, `python-semver-ranges`, `python-shell-sort`,
  `python-shunting-yard`, `python-sieve`, `python-single-flight`, `python-skip-list`,
  `python-smtp-sink`, `python-snowflake-ids`, `python-splay-tree`, `python-sse-api`,
  `python-subset-sum`, `python-suffix-array`, `python-tarjan-scc`, `python-task-queue`,
  `python-text-diff`, `python-three-way-merge`, `python-tim-sort`, `python-time-series-window`,
  `python-topological-sort`, `python-treap`, `python-union-find`, `python-url-signing`,
  `python-van-emde-tree`, `python-version-vectors`, `python-vowel-count`,
  `python-webhook-receiver`, `python-websocket-server`, `python-word-count`,
  `python-z-function`, `sphinx-docs`
- **Node (21)**: `angular-app`, `fastify-api`, `github-action`, `graphql-api`, `hono-api`,
  `nest-api`, `node-cli`, `node-event-sourcing`, `node-http-cache`, `node-http2-api`,
  `node-load-test`, `node-metrics-exporter`, `node-stream-backpressure`, `node-upload-api`,
  `node-worker-pool`, `node-ws-api`, `nuxt-app`, `openapi-spec`, `playwright-e2e`, `prisma-api`,
  `ts-lib`
- **Go (7)**: `go-consistent-hash`, `go-jwt-api`, `go-tcp-framing`, `go-trace-api`, `go-wal-kv`,
  `go-worker`, `grpc-go`
- **Bun (3)**: `bun-api`, `bun-cli`, `bun-sqlite-api`
- **R (2)**: `r-cli`, `r-plumber-api`
- **Ada (2)**: `ada-cli`, `ada-http-api`
- **C (2)**: `c-cli`, `c-http-api`
- **Clojure (2)**: `clojure-cli`, `clojure-ring-api`
- **Csharp (2)**: `aspnet-api`, `dotnet-cli`
- **D (2)**: `d-cli`, `d-http-api`
- **Erlang (2)**: `erlang-cli`, `erlang-cowboy-api`
- **Fortran (2)**: `fortran-cli`, `fortran-http-api`
- **Gleam (2)**: `gleam-cli`, `gleam-mist-api`
- **Groovy (2)**: `groovy-cli`, `groovy-http-api`
- **Haskell (2)**: `haskell-cli`, `haskell-warp-api`
- **Haxe (2)**: `haxe-cli`, `haxe-http-api`
- **Java (2)**: `java-httpserver-api`, `spring-boot`
- **Kotlin (2)**: `kotlin-http-api`, `kotlin-ktor-api`
- **Lisp (2)**: `lisp-cli`, `lisp-http-api`
- **Ocaml (2)**: `ocaml-cli`, `ocaml-http-api`
- **Octave (2)**: `octave-cli`, `octave-http-api`
- **Pascal (2)**: `pascal-cli`, `pascal-http-api`
- **Php (2)**: `laravel-app`, `symfony-app`
- **Powershell (2)**: `powershell-api`, `powershell-cli`
- **Prolog (2)**: `prolog-cli`, `prolog-http-api`
- **Racket (2)**: `racket-api`, `racket-cli`
- **Raku (2)**: `raku-cli`, `raku-http-api`
- **Ruby (2)**: `rails-app`, `ruby-cli`
- **Rust (2)**: `actix-web`, `rust-sqlx-api`
- **Scala (2)**: `scala-cask-api`, `scala-cli`
- **Scheme (2)**: `guile-cli`, `guile-http-api`
- **Sml (2)**: `sml-cli`, `sml-http-api`
- **Swift (2)**: `swift-cli`, `swift-http-api`
- **Tcl (2)**: `tcl-cli`, `tcl-http-api`
- **Typescript (2)**: `deno-api`, `deno-cli`
- **Yaml (2)**: `ansible-role`, `helm-chart`
- **Awk (1)**: `awk-cli`
- **Cobol (1)**: `cobol-cli`
- **Cpp (1)**: `cpp-http-api`
- **Crystal (1)**: `crystal-kemal-api`
- **Dart (1)**: `dart-shelf-api`
- **Docker (1)**: `docker-compose-svc`
- **Elixir (1)**: `phoenix-app`
- **Forth (1)**: `forth-cli`
- **Fsharp (1)**: `fsharp-http-api`
- **Html (1)**: `hugo-site`
- **Jq (1)**: `jq-report`
- **Jsonnet (1)**: `jsonnet-config`
- **Julia (1)**: `julia-api`
- **Latex (1)**: `latex-paper`
- **Lua (1)**: `lua-http-api`
- **Markdown (1)**: `mdbook-docs`
- **Nim (1)**: `nim-http-api`
- **Perl (1)**: `perl-mojolicious-api`
- **Shell (1)**: `bash-cli`
- **Sql (1)**: `sqlite-sql`
- **Vhdl (1)**: `vhdl-sim`
- **Zig (1)**: `zig-http-api`

#### CLI and options

- **`class_name` context key** — a PascalCase identifier (`my-tool` → `MyTool`) for languages that name a module after the project; the Rails template uses it for `module MyTool`.
- **`--package-manager NAME`** — the JavaScript stacks declare the managers they are proven with (`"package_manager": ["npm", "pnpm", "yarn"]`, npm first) and one value writes every command in the project: the install, test, run and build lines in the generated workflow and the README, the lockfile name the README asks you to commit, the `cache:` hint for the CI setup step, a `Prepare <manager>` step that installs the manager itself, and the manager's debug log in `.gitignore`. A manager the stack was not proven with is refused before anything is written, and `newstack update --package-manager` moves a project to a different one with all of those following.
- **`--node MAJOR`** — the JavaScript stacks declare the majors they are proven on (`"node": {"minimum": "22", "versions": ["22", "24"]}`) and one value writes every place a version appears: `engines` in `package.json`, the `node-version` matrix in the generated workflow, and the README. The floor can only go up and only to a major the stack supports — `astro` declares 24 as its own minimum, so `--node 22` is refused instead of scaffolding a project Astro refuses to start. `newstack update --node` moves a project's floor later and every affected file follows.
- **`newstack stacks outdated`** — which installed stacks have moved upstream, answered with one `git ls-remote` per repository rather than a clone, so checking is cheap and writes nothing. Exits 1 when a stack is behind or an origin could not be reached; an unreachable origin is reported as "could not check" instead of hiding the stacks whose state is known. `stacks update` clears it.
- **`newstack stacks update [name]`** — re-pull installed stacks from the repositories they came from, so a fix upstream reaches the machine without a manual reinstall. The clone, the per-stack validation and the name checks all run before anything is replaced: a repository that no longer validates — or one that dropped a stack — leaves the installed copy untouched and names what it could not find. A stack whose files did not change is reported as already current rather than rewritten. Refreshing a stack updates the template; `newstack update <path>` is still what re-applies it to a project, and it keeps local edits.
- **`newstack --python 3.12`** — pick the interpreter floor for the Python stacks, and let one value write every line that names a version: `requires-python`, the ruff target, the trove classifiers, the `python-version` matrix in the generated workflow, the `FROM python:` Docker tag and the README's requires line. Each Python stack declares the versions it has been proven on (`python` in `stack.json`); the floor can only move up, and only to one of them, so `--python 3.9` on `python-cli` or `--python 3.10` on `django` is refused before anything is written. Non-Python stacks say the choice does not apply. The floor is recorded in `.newstack.json`, so `update` keeps it and `update --python 3.13` moves it, rewriting every affected file.
- **`newstack stacks add <git-url>`** — install a stack from any git repository, so a team can keep its own starters without forking newstack. `add` clones shallowly, validates every stack in the repository (one at the root, one per directory, or under `stacks/`; `--dir` picks a subdirectory) before writing anything, refuses a name that already ships with newstack, and records where each stack came from in `sources.json`. `stacks remove` deletes one, `stacks list` shows origin and revision, and installed stacks are marked `[installed]` in `newstack list`, because they are not covered by this repository's CI — `newstack check <name>` is the local equivalent. Stacks live in `$NEWSTACK_HOME/stacks` (default `~/.local/share/newstack/stacks`). `--force` replaces an installed stack.
- **`--license mit|apache-2.0|bsd-3|none`** on `new` (and `update`, to switch later) — the generated `LICENSE` now comes from a licence registry in `data/licenses/` instead of a per-template copy, filled in with `--author` and the current year. `none` ships no file at all, and the choice is stored in `.newstack.json` so `update` keeps honouring it. `adopt` never writes a licence, and `astro` — the one stack whose template had no `LICENSE` — now gets one like every other stack. Closes the last roadmap item.
- **`newstack update`** — re-apply a stack's current template to a project `newstack new` generated, without losing local edits. `new` now writes a `.newstack.json` record (the render context plus a sha256 per file); `update` re-renders the current template with the recorded context and merges per file: untouched files are refreshed, edited files are reported as conflicts and left alone (exit 1) until you pass `--force`, new template files are added, and files the template dropped are reported and only deleted with `--prune` — and only while they still match what newstack wrote. `--dry-run` and `--json` included. Closes the first roadmap item.
- **`newstack outdated`** — the read-only half of the same comparison: reports which recorded files the template has moved past, which files it now adds, and which local edits will conflict. Never writes; exits 1 when there is something to pull, so a CI job or pre-commit hook can ask "is this project still current?".
- **Detect rules accept a glob** — a stack marker may be a pattern, so `haskell-cli` can be detected by `*.cabal` even though the file is named after the project. Literal markers behave exactly as before.

### Fixed

- **`newstack update` no longer rewrites `.newstack.json` when there is nothing to do.** The record carries `updated_at`, so a run over an up-to-date project bumped the timestamp and turned "up to date" into a one-line diff every time. The record is now written only when something actually changed.
- **`fortran-cli` no longer fails its own test suite on a strict filesystem.** The harness used `status='scratch'` units and closed them with `status='delete'`; gfortran on a runner refuses with `Fortran runtime error: File cannot be deleted`, so the `test` step failed even though the counter was correct. The harness now writes and truncates two ordinary files under `build/`, which needs no unlink.
- **The JavaScript stacks pass their tests under yarn, and install under pnpm.** npm and pnpm install the peer dependencies a package asks for, yarn 1 does not, so `yarn test` failed with `Cannot find module '@testing-library/dom'` (`react-vite-ts`) and with `Cannot find package 'vite'` (`next-app-ts`, `node-express-ts`) — projects that were green on two managers and broken on the third the new flag offers. Those dependencies are now pinned in `devDependencies`, `node-express-ts` allows pnpm to build esbuild (`pnpm.onlyBuiltDependencies`), and the pnpm the projects are proven with is pinned to 10 — the version CI installs — because pnpm 12 reads build approval from `pnpm-workspace.yaml` instead and fails such an install with `ERR_PNPM_IGNORED_BUILDS`.
- **`scala-cli` no longer fails on a cold-cache Maven Central hiccup.** scala-cli resolves the pinned Scala version against Maven Central metadata while its cache is empty, and a transient failure there is reported as `Cannot find matching Scala version for '3.3.6'` — a version that plainly exists. Compilation now retries once (in the manifest's verify step and in the shipped workflow), which keeps a genuine compile error failing while a network blip does not.
- **`adopt` recognises a Next.js app as `next-app-ts`.** Every Next project depends on React, so the `"react"` marker matched both stacks and `adopt` would only ever have asked for `--stack`. `next-app-ts` keeps the specific marker and `react-vite-ts` became a `detect_fallback:`, so a Next app resolves to one stack and a plain React project still resolves to the Vite SPA; both directions are tested.
- **`adopt` no longer dead-ends on every Composer and Symfony project.** `symfony-app` detects `bin/console`, which a plain Composer package does not have, so the generic `php-composer-cli` rule became a `detect_fallback:` — a specific marker now wins and a bare `composer.json` still resolves to the CLI stack, with both directions tested.
- **Shipped workflows no longer fail their own exit-code steps.** A `run:` step executes as `bash -e`, so `./bin/app --bogus …; test $? -eq 2` killed the step on the first command and reported the very behaviour the CLI gets right as a failure. The argument and missing-file steps in `bun-cli`, `lua-cli` and `r-cli` now capture `$?` under `set +e` before asserting it, and a structural test rejects the broken shape across every stack.
- **A Haskell project whose name ends in a number now builds.** Cabal reads `tool-2024.cabal` as package `tool` at version `2024` and refuses the file, so a project generated as `tool-2024` failed before its first build. Templates can now use a `cabal_name` context key — the same slug with every all-numeric word given a letter (`tool-v2024`) — and `haskell-cli` names its package with it while the executable keeps the name the user typed.
- **`astro` no longer fails its own check on a moving Node floor.** `astro check` refuses to run below the Node version Astro declares (`>=22.23.4` as of Astro 7.4), and the runner image plus the shared CI step still installed 22.23.3, so the astro job failed while every other stack was green. The repo's Node step now installs 24, the astro scaffold declares `engines.node` and states it in its README, and its shipped workflow tests that LTS instead of a floating 22.x.

## [0.4.0] - 2026-11-03

### Added

- **Twenty-four new stacks**, every one shipped with `detect` + `adopt` metadata so
  `newstack adopt` recognises it too. The registry is at 34 stacks.
  - `flask`, `vue-vite-ts`, `next-app-ts` — the web tier: app factory + blueprint,
    Vue 3 + Vite + TypeScript, Next 16 App Router with Tailwind 4.
  - `chrome-extension` — MV3 extension with a Vite build and `npm run pack`.
  - `data-science` — uv + pandas, summarise/clean helpers over in-memory frames.
  - `go-http`, `rust-axum` — real HTTP services with table tests and graceful shutdown.
  - `astro`, `cpp-cmake-cli`, `terraform-module` — static site, C++20 + CMake + CTest,
    and a validated Terraform module whose `terraform test` cases fail on bad input.
  - `ruby-sinatra`, `java-maven-cli`, `php-composer-cli`, `csharp-cli`,
    `elixir-mix-cli`, `dart-cli` — JSON API on Sinatra, and five CLI stacks spanning
    Maven, Composer, .NET, Mix and pub.
  - `kotlin-cli`, `zig-cli`, `julia-cli`, `nim-cli` — four more ecosystems with no
    package manager between them: Kotlin on Maven (Gradle's wrapper jar cannot be
    templated), Zig with in-source test blocks, Julia on stdlib `Test`, and Nim on
    `unittest`.
  - `perl-cli`, `lua-cli`, `fsharp-cli`, `crystal-cli` — four ecosystems that gate with
    no package install at all: Perl on core-module `Makefile.PL`, Lua 5.4 with a
    hand-rolled spec harness, F# on .NET 8 with a discriminated-union parser, and Crystal
    with `crystal spec` and zero shards.
- **One counter-persistence contract** across the five user-facing JS stacks: state is
  stored under the key `newstack:counter`, clamped to a non-negative integer, and a
  storage failure degrades to memory. Svelte and Next restore in `onMount`/`useEffect`
  so server rendering cannot produce a hydration mismatch.
- **The Chrome extension reports whether it is active on the current page**, instead of
  leaving the user to guess.
- `newstack adopt` guides the user to review a diff instead of printing scaffold
  next-steps that would run the demo.

### Changed

- Template rendering happens fully in memory first, so a template error writes nothing.
- `--name` is now sanitised against Java's reserved words as well as Python's: `--name
  static` used to render `package static;`, which no Java compiler accepts.
- The registry no longer validates every stack on load: a half-built stack directory is
  reported by `list` and `check --all` instead of breaking them.

### Fixed

- Shipped Crystal workflows pin `crystal-lang/install-crystal@v1.9.5` instead of `@v1`:
  that action publishes exact tags only, so a moving major resolved to nothing and the
  job died before its first step. The bare-major guard in the test suite now covers every
  action known to be in that category instead of `astral-sh/setup-uv` alone.
- Shipped Node workflows no longer use `actions/setup-node` with `cache: npm` while the
  template has no lockfile — that fails inside the setup action before any install runs,
  and only a real runner proved it. A regression test now fails if any shipped workflow
  needs a file the template does not ship.
- `data-science` summarised across mixed units (counts and revenue averaged together);
  it now reports per-column means, and the tests assert the meaningful number.
- Accessibility and copy pass over the six user-facing templates: focus moves to the
  target of an in-page scroll, counters are announced through `role="status"`, controls
  name their action rather than their state, and `:focus-visible` is styled everywhere.


## [0.3.0] - 2026-11-02

### Added

- **`newstack adopt <dir>`** — retrofit a stack's infrastructure onto a project that already
  has code. Additive by construction: an existing file is never opened for writing, and any
  change that would need a merge inside a file is reported as a manual step instead.
  - Auto-detects the stack from the project's own markers (`go.mod`, `Cargo.toml`,
    `manage.py`, `pyproject.toml`/`package.json` contents, a bare `index.html`); ambiguous
    matches print candidates and exit 2; `--stack` overrides.
  - Copies infrastructure only — workflows, `.gitignore`, lint/type config — never a
    README, LICENSE, `pyproject.toml`, `package.json`, `go.mod` or source file.
  - `--dry-run` reports without writing; re-running is a no-op; `--json` for scripting.
  - `--with-tests` (experimental) also copies the stack's starter tests.
- Manifest keys `detect`, `detect_fallback`, `adopt` and `adopt_tests`, validated by the
  registry and by tests that require every adoptable path to exist and to be infrastructure.

### Changed

- `newstack new` and `adopt` share one step formatter, so an unknown `{placeholder}` in a
  manifest's `next_steps` prints literally instead of raising `KeyError`.

## [0.2.0] - 2026-11-02

### Added

- Four new stacks, all verified the same way as the original six:
  - `go-cli` — stdlib `flag` parsing, table tests, vet/test/build gates.
  - `rust-cli` — std-only parsing, lib+bin split, fmt/clippy/test/release gates.
  - `django` — Django 6.1, config/core split, SQLite, pytest-django, and a
    migration-drift step that fails when a model changes without a migration.
  - `svelte-kit-ts` — SvelteKit 3 with Svelte 5 runes, Vitest, static adapter build.
- CI runs one job per stack (ten in total), with Go and Rust toolchains installed only
  for the jobs that need them.
- Docs drift tests: the README table and the CI matrix must both list every registered
  stack, and the README may not hardcode a stack count.

### Changed

- Install instructions now point at PyPI (`uvx newstack`, `uv tool install newstack`).

## [0.1.0] - 2026-11-02

### Added

- `newstack new <stack> <path>` — render a stack, initialise git, first commit.
- `newstack new … --github [OWNER/REPO]` — create the GitHub repository and push.
- `newstack list` — every stack with its toolchain requirements, `--json` supported.
- `newstack check <stack…> | --all` — generate into a temp dir and run the stack's own
  verification steps (`install`, `lint`, `test`, `build`), reported per step.
- `newstack doctor` — which toolchains are installed, which stacks can be verified here.
- Six stacks: `python-lib`, `python-cli`, `fastapi`, `react-vite-ts`, `node-express-ts`,
  `static-site`.
- Stack registry is extensible through the `NEWSTACK_STACKS` environment variable.
- Zero runtime dependencies: standard library only.
