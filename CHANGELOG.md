# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`hugo-site`**: a Hugo content site rather than a CLI — hand-written `layouts/` and
  partials, no theme and no JavaScript, TOML front matter, a `{{< note >}}` shortcode, and a
  stylesheet that is minified and fingerprinted (with subresource integrity) by Hugo's asset
  pipeline. `make test` renders the whole site into a temporary directory and asserts on the
  HTML — partials ran, the shortcode expanded, headings got ids, the sitemap and RSS feed
  exist, `robots.txt` points at the sitemap, no dev-only script leaked into a built page — and
  it writes deliberately malformed front matter to require the build to *fail*. Six verify
  steps, including a negative one and a real `hugo server` fetch.
- **`pascal-cli`**: a `wc`-style counter in Free Pascal on `fpc` and `make`, RTL only —
  bytes are read raw and folded once, arguments are parsed by hand, and the terminal lives
  behind a record of three function pointers, so the suite drives exit codes and rows
  without spawning a process. 47 assertions, and the shipped workflow checks the suite,
  the exit codes, stdin and byte-for-byte parity with `wc`.
- **`lisp-cli`**: a `wc`-style counter in Common Lisp on SBCL, standard library only —
  bytes are read as `(unsigned-byte 8)` and folded once, arguments are parsed by hand, and
  the program takes a structure of four functions so the suite drives it without a process.
  69 assertions, and the shipped workflow checks the suite, the exit codes, stdin and
  byte-for-byte parity with `wc`.
- **`prolog-cli`**: a `wc`-style counter in SWI-Prolog with no dependencies outside the
  standard library — counting works on a stream, arguments are parsed by hand, output goes
  through two writer closures so the whole contract is testable, and a four-predicate
  harness runs 58 assertions. The shipped workflow checks the suite, the exit codes, stdin
  and byte-for-byte parity with `wc` on five fixtures.
- **`nest-api`**: a NestJS 12 service — a feature module with a controller, a service and a
  pipe that rejects a missing `text` with 400, six unit tests plus four end-to-end tests
  over supertest, and `GET /stats?text=...` returning `{lines, words, bytes}`. NestJS 12
  ships no CommonJS build, so the project is ESM (`"type": "module"`, `.js` import
  suffixes) and `jest.config.js` strips that suffix for ts-jest. The five verify steps
  install, typecheck, test, build and then serve the app and query it live.
- **`octave-cli`**: a wc-style CLI in plain Octave — the counting core, the argument
  parser and the runner live in a `+textstat` package directory, the runner takes its
  environment as a struct of function handles, and a 58-check suite needs no
  framework. The seven verify steps cover the suite, the help text, both exit-code
  paths, standard input, the `-` operand and `wc` parity. Single-quoted Octave strings
  do not interpret escapes, so the fixtures are built with `sprintf`.
- **`ada-cli`**: Ada on GNAT — a counting core that works on bytes, an argv parser with
  `--` and short clusters, and a dependency-free harness of 71 checks; the runner takes
  its two output subprograms as parameters, so only `main.adb` touches the real stdin.
  Eight checks, including a `stdin` step, a `dash-operand` step and byte-exact `wc` parity.
- **`fortran-cli` stack.** Fortran 2018 on `gfortran` and `make`, with no test framework: the counting core takes bytes through a `counter_t`, the runner takes its output units as arguments so the 51-check suite reads what the tool would have printed, and stdin is read a byte at a time through a stream connection to `/dev/stdin` — the only byte-exact option in Fortran.
- **`vhdl-sim` stack** — a synthesizable VHDL counter plus a self-checking testbench on GHDL: every
  check is an `assert ... severity error` and `run.sh` passes `--assert-level=error`, so a wrong design
  is a non-zero exit code rather than a waveform for a human to read. The `inject_fault` generic is the
  teeth test — the shipped workflow runs the testbench a second time with the fault enabled and
  requires that run to fail. `*.vhd` is the detection marker.
- **`deno-cli` stack** — a TypeScript project on Deno, with no `package.json` and no build step: the
  runtime is also the typechecker and the test runner. Counting works on `Uint8Array` so `wc` parity
  holds for UTF-8 and control characters, the argv parser is a pure function, and the runner takes an
  object of four functions so 24 `Deno.test` cases run without touching a file — while the shipped
  `stdin` check still pipes real text through the real command. The wrapper grants only `--allow-read`.
  `deno.json` is the detection marker.
- **`racket-cli` stack** — a Racket project on the core distribution, no packages and no build step.
  Counting works on `bytes` so `wc` parity holds for UTF-8 and control characters, the argv parser is
  a struct with no side effects, and the runner takes a `struct io` of four funs so 54 `rackunit`
  checks run without touching a file — while the shipped `stdin` check still pipes real text through
  the real command. `*.rkt` is the detection marker.
- **`erlang-cli` stack** — an Erlang project on plain OTP and `make`, no rebar and no hex packages.
  Counting works on binaries so `wc` parity holds for UTF-8 and control characters, the argv parser
  is hand-written, and the runner takes a map of four funs (`read_file`, `read_stdin`, `out`, `err`)
  so 42 eunit tests run without touching a file — while the shipped `stdin` check still pipes real
  text through the real binary, because a fake boundary cannot see a broken stdin path. The wrapper
  builds on first use. `Makefile` containing `erlc` is the detection marker.
- **`tcl-cli` stack** — a Tcl project on plain `tclsh`, no package manager and no build step. The
  counting core works on byte strings (`binary scan cu*`) so `wc` parity holds for UTF-8 and control
  characters, the argv parser is hand-written, and the runner takes a dictionary of `readFile`,
  `readStdin`, `out` and `err` so 40 checks run without a process — while the shipped `stdin` check
  still pipes real text through the real binary, because a fake boundary cannot see a broken stdin
  path. `*.tcl` is the detection marker.
- **`rails-app` stack** — Rails 8.1 on Ruby 3.2+: the counting lives in
  `app/services/text_stat.rb` (a plain class, no Rails code), `StatsController` turns it into
  `GET /stats?text=...`, and an `ActionDispatch::IntegrationTest` goes through the router so a
  broken route fails the suite. `bin/setup` writes gems into `vendor/bundle` via the committed
  `.bundle/config` instead of the system gem directory, and the five checks cover install,
  `bin/rails test`, `wc` parity through `bin/rails runner`, and a live request against a
  server started on its own port. No encrypted credentials are shipped.
- **`ansible-role` stack** — a Galaxy-shaped role (defaults, vars, tasks, handlers, templates,
  files, meta, `tests/playbook.yml` + `tests/verify.yml`) that installs a small POSIX counter
  and refuses an unsupported `textstat_columns` value through an `assert`. Fourteen checks
  include idempotence (`changed=0` on the second run), a `--check` dry run that writes
  nothing, and two override runs proving the defaults actually drive the output.
- **`class_name` context key** — a PascalCase identifier (`my-tool` → `MyTool`) for languages
  that name a module after the project; the Rails template uses it for `module MyTool`.
- **`--package-manager NAME`** — the JavaScript stacks declare the managers they are proven
  with (`"package_manager": ["npm", "pnpm", "yarn"]`, npm first) and one value writes every
  command in the project: the install, test, run and build lines in the generated workflow
  and the README, the lockfile name the README asks you to commit, the `cache:` hint for the
  CI setup step, a `Prepare <manager>` step that installs the manager itself, and the
  manager's debug log in `.gitignore`. A manager the stack was not proven with is refused
  before anything is written, and `newstack update --package-manager` moves a project to a
  different one with all of those following.
- **`--node MAJOR`** — the JavaScript stacks declare the majors they are proven on
  (`"node": {"minimum": "22", "versions": ["22", "24"]}`) and one value writes every place a
  version appears: `engines` in `package.json`, the `node-version` matrix in the generated
  workflow, and the README. The floor can only go up and only to a major the stack supports —
  `astro` declares 24 as its own minimum, so `--node 22` is refused instead of scaffolding a
  project Astro refuses to start. `newstack update --node` moves a project's floor later and
  every affected file follows.
- **`newstack stacks outdated`** — which installed stacks have moved upstream, answered with
  one `git ls-remote` per repository rather than a clone, so checking is cheap and writes
  nothing. Exits 1 when a stack is behind or an origin could not be reached; an unreachable
  origin is reported as "could not check" instead of hiding the stacks whose state is known.
  `stacks update` clears it.
- **`newstack stacks update [name]`** — re-pull installed stacks from the repositories they
  came from, so a fix upstream reaches the machine without a manual reinstall. The clone,
  the per-stack validation and the name checks all run before anything is replaced: a
  repository that no longer validates — or one that dropped a stack — leaves the installed
  copy untouched and names what it could not find. A stack whose files did not change is
  reported as already current rather than rewritten. Refreshing a stack updates the
  template; `newstack update <path>` is still what re-applies it to a project, and it keeps
  local edits.
- **`newstack --python 3.12`** — pick the interpreter floor for the Python stacks, and let
  one value write every line that names a version: `requires-python`, the ruff target, the
  trove classifiers, the `python-version` matrix in the generated workflow, the
  `FROM python:` Docker tag and the README's requires line. Each Python stack declares the
  versions it has been proven on (`python` in `stack.json`); the floor can only move up,
  and only to one of them, so `--python 3.9` on `python-cli` or `--python 3.10` on `django`
  is refused before anything is written. Non-Python stacks say the choice does not apply.
  The floor is recorded in `.newstack.json`, so `update` keeps it and `update --python 3.13`
  moves it, rewriting every affected file.
- **`newstack stacks add <git-url>`** — install a stack from any git repository, so a team
  can keep its own starters without forking newstack. `add` clones shallowly, validates
  every stack in the repository (one at the root, one per directory, or under `stacks/`;
  `--dir` picks a subdirectory) before writing anything, refuses a name that already ships
  with newstack, and records where each stack came from in `sources.json`. `stacks remove`
  deletes one, `stacks list` shows origin and revision, and installed stacks are marked
  `[installed]` in `newstack list`, because they are not covered by this repository's CI —
  `newstack check <name>` is the local equivalent. Stacks live in `$NEWSTACK_HOME/stacks`
  (default `~/.local/share/newstack/stacks`). `--force` replaces an installed stack.
- **`--license mit|apache-2.0|bsd-3|none`** on `new` (and `update`, to switch later) —
  the generated `LICENSE` now comes from a licence registry in `data/licenses/` instead of
  a per-template copy, filled in with `--author` and the current year. `none` ships no
  file at all, and the choice is stored in `.newstack.json` so `update` keeps honouring
  it. `adopt` never writes a licence, and `astro` — the one stack whose template had no
  `LICENSE` — now gets one like every other stack. Closes the last roadmap item.
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

- **`fortran-cli` no longer fails its own test suite on a strict filesystem.** The harness
  used `status='scratch'` units and closed them with `status='delete'`; gfortran on a
  runner refuses with `Fortran runtime error: File cannot be deleted`, so the `test` step
  failed even though the counter was correct. The harness now writes and truncates two
  ordinary files under `build/`, which needs no unlink.
- **The JavaScript stacks pass their tests under yarn, and install under pnpm.** npm and
  pnpm install the peer dependencies a package asks for, yarn 1 does not, so `yarn test`
  failed with `Cannot find module '@testing-library/dom'` (`react-vite-ts`) and with
  `Cannot find package 'vite'` (`next-app-ts`, `node-express-ts`) — projects that were green
  on two managers and broken on the third the new flag offers. Those dependencies are now
  pinned in `devDependencies`, `node-express-ts` allows pnpm to build esbuild
  (`pnpm.onlyBuiltDependencies`), and the pnpm the projects are proven with is pinned to 10 —
  the version CI installs — because pnpm 12 reads build approval from `pnpm-workspace.yaml`
  instead and fails such an install with `ERR_PNPM_IGNORED_BUILDS`.
- **`scala-cli` no longer fails on a cold-cache Maven Central hiccup.** scala-cli resolves the
  pinned Scala version against Maven Central metadata while its cache is empty, and a transient
  failure there is reported as `Cannot find matching Scala version for '3.3.6'` — a version
  that plainly exists. Compilation now retries once (in the manifest's verify step and in the
  shipped workflow), which keeps a genuine compile error failing while a network blip does not.
- **`adopt` recognises a Next.js app as `next-app-ts`.** Every Next project depends on React,
  so the `"react"` marker matched both stacks and `adopt` would only ever have asked for
  `--stack`. `next-app-ts` keeps the specific marker and `react-vite-ts` became a
  `detect_fallback:`, so a Next app resolves to one stack and a plain React project still
  resolves to the Vite SPA; both directions are tested.
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
