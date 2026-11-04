# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`newstack update`** — re-apply a stack's current template to a project `newstack new`
  generated, without losing local edits. `new` now writes a `.newstack.json` record (the
  render context plus a sha256 per file); `update` re-renders the current template with
  the recorded context and merges per file: untouched files are refreshed, edited files
  are reported as conflicts and left alone (exit 1) until you pass `--force`, new
  template files are added, and files the template dropped are reported and only deleted
  with `--prune` — and only while they still match what newstack wrote. `--dry-run` and
  `--json` included. Closes the first roadmap item.
- **`newstack outdated`** — the read-only half of the same comparison: reports which
  recorded files the template has moved past, which files it now adds, and which local
  edits will conflict. Never writes; exits 1 when there is something to pull, so a CI job
  or pre-commit hook can ask "is this project still current?".
- **Two stacks: `bun-cli` and `r-cli`** — `bun-cli` is a zero-dependency Bun +
  TypeScript CLI whose whole test suite is the built-in `bun:test` runner, so a fresh
  clone runs `bun test` offline with no `node_modules` at all; `r-cli` is the same
  wc-style tool in **base R only** (no testthat, no CRAN, no renv) with a hand-rolled
  assertion harness and `Rscript` as the entry point. Both follow the counting-library +
  thin-CLI split and the 0/2/1 exit contract, and both are verified line-for-line against
  real `wc -l -w -c`.
- **`symfony-app` stack** — a Symfony 7 web application on PHP 8.3 + Composer, not a
  console toy: a real kernel with `config/` bundles and routes, a `GET /` route returning
  JSON from an injected pure `TextStats` service, a kernel-booting PHPUnit 11 functional
  test next to the unit test, a working `bin/console`, and a shipped CI workflow with
  PHPUnit plus a console smoke step. Autowiring means the service needs no container
  configuration.
- **`ocaml-cli` stack** — OCaml 4.14 on dune 3.14 with no opam packages at all: pure
  `Counts`/`Options`/`Runner` modules (`(wrapped false)`, no `open` boilerplate in the
  tests), a stdlib-only harness that prints a pass/fail tally and exits non-zero, and a
  shell wrapper around the dune executable so the dashed project name survives dune's
  "executable name must be a module identifier" rule. Verified against `wc -l -w -c` on
  plain, no-trailing-newline, multibyte-UTF-8, empty and control-character files.
- **`helm-chart` stack** — a Kubernetes Helm chart for one stateless HTTP service,
  the first stack that is not a program: named templates in `_helpers.tpl`, a Deployment
  with a hardened `securityContext` and probes, a Service, an optional ServiceAccount,
  and a `values.schema.json` that helm enforces on every `lint`, `template` and `install`
  (so `--set replicaCount=0` fails the chart rather than the cluster). It also ships the
  chart's own `helm test` hook — a pod that curls the Service — and seven checks: lint,
  render, values plumbing, schema rejection, hook rendering, release-name plumbing and
  the hardened defaults, all of which run without a cluster or any plugin.
- **`gleam-cli` stack** — a Gleam 1.19 CLI on Erlang/OTP 27 with no hex packages beyond
  `gleam_stdlib`: pure `Counts`/`Options`/`Runner` modules, a hand-rolled test harness
  (`gleam test` runs the tally and exits non-zero on failure), and one small Erlang module
  for the three things Gleam's standard library has no answer for — argv, stdin and the
  process exit code. `Runner.run` *returns* the 0/1/2 code and only the entry point calls
  `erlang:halt`, so the exit contract is asserted without spawning a process. `gleam
  format --check` is part of the shipped workflow. Verified against `wc -l -w -c`.
- **`scala-cli` stack** — a Scala 3 CLI where the build definition *is* the source:
  `project.scala` holds three `//> using` directives (Scala 3.3.6, main class, munit) and
  there is no `build.sbt`, no `pom.xml` and no build server (`--server=false`, so no Bloop
  daemon is left running). Counting is pure, `Runner.run` takes an `Io` instead of touching
  the world, so the 0/1/2 exit contract and the `wc` column layout are asserted in munit
  without spawning a process. The generated project ships a workflow that installs the
  single scala-cli binary at a pinned version.
- **`haskell-cli` stack** — a GHC 9.4 / cabal CLI whose only dependencies are `base` and
  `bytestring`, both of which ship with GHC, so a generated project builds offline once
  cabal has an index. Counting is a strict `foldl'` over the bytes; `Runner.run` takes an
  `Io` record, so the 0/1/2 exit contract, the `-` stdin label and the `total` row are
  asserted in a 47-check hand-written harness instead of a test framework. `wc` parity is
  a verify step and part of the shipped workflow.
- **Detect rules accept a glob** — a stack marker may be a pattern, so `haskell-cli` can
  be detected by `*.cabal` even though the file is named after the project. Literal
  markers behave exactly as before.
- **`dotnet-cli` stack** — a .NET 8 C# CLI laid out the way a .NET solution actually is:
  a `<name>.sln` with the app project and a separate xUnit project under `tests/`,
  a pure `TextStat` counter that never touches I/O, a hand-written `Options.Parse` that
  returns `{figures, files, status}` instead of throwing, and a `Cli.Run(args, out, err)`
  that *returns* the 0/1/2 exit code so tests assert the contract without spawning a
  process. `-l -w -c` combine like real `wc`, `--` ends flag parsing, and several files
  get a `total` row. Verified against `wc -l -w -c`.
- **`spring-boot` stack** — a Java 21 Spring Boot 3 web service rather than a console
  tool: `StatsService` is pure counting, `StatsController` exposes `GET /stats?text=…`
  (400 when the parameter is missing) and `GET /`, and the JUnit 5 suite covers the
  service directly plus the controller through `MockMvc` — 5 tests, no running server
  needed. A Maven wrapper is included, the jar is `target/<name>.jar`, and the shipped
  workflow runs `mvn -B -ntp verify` plus a live endpoint smoke test on a port the app is
  told to use, so a scaffolded service proves its own HTTP surface in CI.
- **`clojure-cli` stack** — a Clojure CLI tool on `deps.edn` and `clojure -M:test`, with
  no Leiningen and no third-party libraries: `textstat.counts` folds over raw bytes,
  `textstat.options` parses argv by hand, `textstat.cli/run` returns the exit code as a
  value so the `clojure.test` suite (28 tests, 54 assertions) never spawns a process, and
  only `textstat.main` touches the filesystem, `System/in` and `System/exit`. The seven
  shipped checks include stdin, so a broken real-input path cannot hide behind the fake
  I/O record the unit tests inject.
- **`swift-cli` stack** — a Swift 6 CLI on SwiftPM with XCTest and no packages beyond
  the toolchain: `TextStat` is a pure library (`ofBytes` over raw bytes, `add`, the
  right-aligned row layout), `Options.parse` handles `-l/-w/-c`, the long flags, `--`, `-`
  and help/version by hand, and `CLI.run(_:io:)` returns the exit code against a struct of
  closures so 29 XCTest cases never spawn a process. Only `main.swift` touches the real
  files, stdin and `exit`; the wrapper builds in release mode and execs the product. The
  shipped checks include stdin and a `wc -l -w -c` parity loop, and `total` rows follow
  `wc` even when an operand is unreadable.

### Fixed

- **`adopt` no longer dead-ends on every Composer and Symfony project.** `symfony-app`
  detects `bin/console`, which a plain Composer package does not have, so the generic
  `php-composer-cli` rule became a `detect_fallback:` — a specific marker now wins and a
  bare `composer.json` still resolves to the CLI stack, with both directions tested.
- **Shipped workflows no longer fail their own exit-code steps.** A `run:` step executes
  as `bash -e`, so `./bin/app --bogus …; test $? -eq 2` killed the step on the first
  command and reported the very behaviour the CLI gets right as a failure. The argument
  and missing-file steps in `bun-cli`, `lua-cli` and `r-cli` now capture `$?` under
  `set +e` before asserting it, and a structural test rejects the broken shape across
  every stack.
- **A Haskell project whose name ends in a number now builds.** Cabal reads
  `tool-2024.cabal` as package `tool` at version `2024` and refuses the file, so a project
  generated as `tool-2024` failed before its first build. Templates can now use a
  `cabal_name` context key — the same slug with every all-numeric word given a letter
  (`tool-v2024`) — and `haskell-cli` names its package with it while the executable keeps
  the name the user typed.
- **`astro` no longer fails its own check on a moving Node floor.** `astro check` refuses
  to run below the Node version Astro declares (`>=22.23.4` as of Astro 7.4), and the
  runner image plus the shared CI step still installed 22.23.3, so the astro job failed
  while every other stack was green. The repo's Node step now installs 24, the astro
  scaffold declares `engines.node` and states it in its README, and its shipped workflow
  tests that LTS instead of a floating 22.x.

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
