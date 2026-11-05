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
| `react-vite-ts` | React 19 + Vite + TS, Vitest + Testing Library, typecheck + build | `node`, `npm`/\`pnpm\`/\`yarn` |
| `vue-vite-ts` | Vue 3 + Vite + TS, Vitest + @vue/test-utils, typecheck + build | `node`, `npm`/\`pnpm\`/\`yarn` |
| `next-app-ts` | Next.js App Router + TS + Tailwind 4, Vitest + Testing Library | `node`, `npm`/\`pnpm\`/\`yarn` |
| `chrome-extension` | MV3 extension: popup + service worker + content script, `npm run pack` → extension.zip | `node`, `npm`/\`pnpm\`/\`yarn` |
| `astro` | Astro + TS content site: typed frontmatter, Vitest unit tests, `astro check` + static build | `node`, `npm`/\`pnpm\`/\`yarn` |
| `ts-lib` | Publishable TS package: tsup ESM+CJS+`.d.ts`, split `exports` types per format, vitest, publint `--strict` and `npm pack --dry-run` gates | `node`, `npm`/\`pnpm\`/\`yarn` |
| `data-science` | pandas workspace: testable DataFrame helpers, pytest, sample notebook | `uv` |
| `sphinx-docs` | Sphinx site over a real package: autodoc, executed doctests, `-W` build, docs tested in CI | `uv` |
| `node-express-ts` | Express 5 API, typed handlers, supertest tests | `node`, `npm`/\`pnpm\`/\`yarn` |
| `hono-api` | Hono JSON API: `createApp()` returned as a value so tests use `app.request()` with no socket, `tsc` build (no bundler), `node dist/server.js` | `node`, `npm`/\`pnpm\`/\`yarn` |
| `openapi-spec` | OpenAPI 3.1 first: spectral lint with warnings as failures, redocly bundle + HTML reference, contract tests validating live responses against the bundle | `node`, `npm`/\`pnpm\`/\`yarn` |
| `graphql-api` | GraphQL Yoga with schema-first SDL: typed resolvers, a depth-limit plugin that answers `QUERY_TOO_DEEP` instead of hanging, `yoga.fetch()` tests with no socket, `tsc` build | `node`, `npm`/\`pnpm\`/\`yarn` |
| `dbt-project` | Analytics engineering on dbt + DuckDB: seed → staging view → mart table, `+schema` per layer, generic + singular tests, `dbt build` runs models and tests, and a read-only script re-checks the numbers | `uv`, `git` |
| `nest-api` | NestJS 12 service: module/controller/service wiring, a validating pipe, supertest end-to-end tests, ESM throughout | `node`, `npm`/\\`pnpm\\`/\\`yarn` |
| `svelte-kit-ts` | SvelteKit + TS, Svelte 5 runes component, Vitest, static adapter build | `node`, `npm`/\`pnpm\`/\`yarn` |
| `github-action` | JavaScript action on `node24` (no Docker, zero deps): pure counting core, Markdown step summary, `GITHUB_OUTPUT` writes, `node:test` suite that spawns the real entry point | `node` |
| `go-cli` | stdlib-only Go CLI: `flag` parsing, table tests, vet/test/build gates | `go` |
| `go-http` | Go HTTP service on `net/http`: JSON routes, `httptest` suite, graceful shutdown | `go` |
| `grpc-go` | Protobuf-first Go service: `buf` lint/codegen, `bufconn` tests, real-socket smoke test, health service and reflection | `go` |
| `rust-cli` | std-only Rust CLI: lib+bin split, fmt/clippy/test/release-build gates | `cargo` |
| `rust-axum` | axum service: typed routes, shared state, `tower` oneshot tests, fmt/clippy | `cargo` |
| `c-cli` | C11 CLI: Makefile lib+bin split, assert-header test suite, `-Wall -Wextra -Wpedantic -Werror` from the first commit | `cc`, `make` |
| `cpp-cmake-cli` | C++20 CLI: CMake lib+bin split, CTest suite, warning-clean GCC/Clang build | `cmake`, `g++` |
| `terraform-module` | Reusable module: validated inputs, computed tags, `terraform test` cases incl. a rejected input | `terraform` |
| `ansible-role` | Galaxy-shaped Ansible role: validated inputs, idempotent tasks, a handler, molecule-free playbook + assert playbooks | `ansible-playbook` |
| `ruby-sinatra` | Sinatra JSON API: modular app, RSpec + rack-test suite, RuboCop, committed lockfile | `ruby`, `bundle` |
| `rails-app` | Rails 8 JSON app: a service object for the counting, an integration test that goes through the router, SQLite, committed lockfile | `ruby`, `bundle` |
| `java-maven-cli` | Java 21 CLI on Maven: pure counting logic, 21 JUnit 5 tests, runnable jar | `java`, `mvn` |
| `spring-boot` | Java 21 Spring Boot 3 web service on Maven: a wc-style `/stats` endpoint, a pure service, and a JUnit 5 + MockMvc suite | `java`, `mvn` |
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
| `zig-cli` | Zig 0.17 CLI: counting module with in-source test blocks, `zig build test`, no runtime | `zig` |
| `julia-cli` | Julia CLI: pure counting module, `Test` stdlib suite, zero external packages | `julia` |
| `nim-cli` | Nim CLI: pure counting module, `unittest` suite that also checks exit codes, `nimble build` binary | `nim`, `nimble` |
| `nim-http-api` | Nim JSON service: counting core, a pure `route()` covering every status code, `asynchttpserver` on top — no dependencies at all | `nim`, `nimble` |
| `perl-cli` | Perl CLI on core modules only: `Makefile.PL` + `Test::More` suite, no CPAN install step | `perl`, `make` |
| `lua-cli` | Lua 5.4 CLI: stdlib-only modules, a hand-rolled spec harness, zero luarocks dependencies | `lua5.4` |
| `fsharp-cli` | F# on .NET 8: pure counting core, `Mode` discriminated union parser, xUnit suite that launches the binary for its exit codes | `dotnet` |
| `crystal-cli` | Crystal CLI: stdlib-only modules, `crystal spec` suite, compiled binary with a 0/2/1 exit contract | `crystal` |
| `crystal-kemal-api` | Crystal service on Kemal: counting rules and the whole route table are pure functions under `crystal spec`, plus a real socket check | `crystal`, `shards` |
| `bun-cli` | Bun CLI: pure counting module, hand-written option parser, zero-dependency `bun:test` suite | `bun` |
| `bun-api` | Bun JSON service: one `Request`→`Response` handler, `Bun.serve`, `bun:test` suites, `tsc --noEmit` via `bun run typecheck`, real socket smoke test | `bun` |
| `r-cli` | R CLI on base R only: pure counting function, hand-written option parser, dependency-free test harness | `Rscript` |
| `ocaml-cli` | OCaml CLI on dune: pure counting library, hand-written option parser, stdlib-only test harness, zero opam dependencies | `ocaml`, `dune` |
| `static-site` | HTML/CSS/JS page, `node:test` suite, GitHub Pages deploy workflow | `node` |
| `hugo-site` | Content site on Hugo: hand-written layouts and partials, a shortcode, fingerprinted CSS, sitemap and RSS, assertion suite that renders into a temp dir | `hugo` |
| `helm-chart` | Kubernetes Helm chart: schema-validated values, named templates, hardened Deployment/Service, lint+render checks with no cluster | `helm` |
| `gleam-cli` | Gleam CLI: pure counting module, hand-written option parser, stdlib-only test harness, Erlang helper for argv/stdin/exit codes | `gleam` |
| `scala-cli` | Scala 3 CLI built with scala-cli (no sbt): pure counting core, hand-rolled argv parser, munit suites, wrapper that returns the process exit code | `scala-cli`, `java` |
| `haskell-cli` | Haskell CLI on GHC and cabal: pure counting core, hand-rolled argv parser, dependency-free test harness, I/O behind a record | `ghc`, `cabal` |
| `clojure-cli` | Clojure CLI on `deps.edn` (no Leiningen): pure counting core, hand-rolled argv parser, `clojure.test` suites, I/O behind a record | `clojure`, `java` |
| `clojure-ring-api` | Ring JSON service on `deps.edn`: the handler is a plain request-map function, `ring.mock` drives the routes with no port, Jetty serves it, `clojure.test` gates it | `clojure`, `java` |
| `swift-cli` | Swift 6 CLI on SwiftPM: pure counting core, hand-rolled argv parser, XCTest suites, I/O behind a struct of closures | `swift` |
| `tcl-cli` | Tcl CLI on plain `tclsh`: byte-level counting core, hand-rolled argv parser, dependency-free test harness, I/O behind a dictionary | `tclsh` |
| `erlang-cli` | Erlang CLI on plain OTP and `make`: byte-level counting core, hand-rolled argv parser, eunit suites, I/O behind a map of funs | `erl`, `erlc`, `make` |
| `racket-cli` | Racket CLI on the core distribution: byte-counting core, struct-based argv parser, `rackunit` suites, I/O behind a struct of funs | `racket`, `raco` |
| `deno-cli` | TypeScript CLI on Deno: byte-counting core, pure argv parser, `Deno.test` suites, I/O behind an object of functions | `deno` |
| `deno-api` | Deno 2 JSON service: one `Request`→`Response` handler, `Deno.serve`, std assertions, check/fmt/lint gates and a real socket smoke test | `deno` |
| `vhdl-sim` | VHDL design with a self-checking testbench on GHDL: one clocked process, assertion-driven simulation, a run script that fails CI on a wrong design | `ghdl` |
| `fortran-cli` | Fortran CLI on `gfortran` and `make`: byte-exact counting core, hand-rolled argv parser, dependency-free test harness, output units injected | `gfortran`, `make` |
| `ada-cli` | Ada CLI on GNAT: byte-exact counting core, hand-rolled argv parser, dependency-free test harness, output through two subprogram parameters | `gnatmake`, `make` |
| `octave-cli` | Octave CLI on plain `octave`: counting core in a `+textstat` package, hand-rolled argv parser, dependency-free suite, environment injected as function handles | `octave` |
| `prolog-cli` | SWI-Prolog CLI: byte-exact counting over a stream, hand-rolled argv parser, a four-predicate test harness, output behind two writer closures | `swipl` |
| `lisp-cli` | Common Lisp CLI on SBCL: byte-exact counting core, hand-rolled argv parser, dependency-free test harness, I/O through a structure of functions | `sbcl` |
| `pascal-cli` | Free Pascal CLI on FPC and `make`: byte-exact counting unit, hand-written argv parser, dependency-free test suite, terminal behind a record of function pointers | `fpc`, `make` |
| `bash-cli` | Bash CLI on plain `bash` and `shellcheck`: counting in bash itself (no `wc`, no `awk`), hand-rolled argv parser, dependency-free test harness, terminal behind sourced functions | `bash`, `shellcheck` |
| `cobol-cli` | COBOL CLI on GNUCOBOL: byte-exact counting over a one-byte sequential read, hand-rolled argv parser reading `/proc/self/cmdline`, a COBOL unit driver plus a shell suite, I/O in one program | `cobc`, `make` |
| `guile-cli` | Scheme CLI on GNU Guile: bytevector counting core, hand-rolled argv parser, dependency-free harness, ports behind a record of procedures | `guile` |
| `raku-cli` | Raku CLI on Rakudo: `Buf` counting core, hand-rolled argv parser, dependency-free harness, the four side effects handed in as closures | `raku` |
| `groovy-cli` | Groovy CLI on the plain Groovy runtime: byte-array counting core, hand-rolled argv parser, dependency-free harness, the four side effects handed in as closures | `groovy`, `java` |
| `awk-cli` | awk CLI on `gawk`: counting with `RS="\0"` so each file is one record, hand-rolled argv parser, dependency-free harness, the report built before anything is printed | `gawk` |
| `forth-cli` | Forth CLI on `gforth`: counting over a memory block with a loop and `c@`, hand-rolled argv parser, a four-word test harness, terminal reads behind one file | `gforth` |
| `sqlite-sql` | SQL reporting project on SQLite: schema with `CHECK` constraints, views that hold the arithmetic, one `SELECT` per report, assertions over exact cents | `sqlite3`, `make` |
| `jq-report` | Reports over a JSON access log as plain jq programs: status counts, busiest paths, slowest requests, bytes per day, error rate, behind a shell command with a tested exit-code contract | `jq`, `make` |
| `powershell-cli` | PowerShell 7 CLI: byte loop over the payload, hand-rolled argv parser, I/O behind a hashtable of scriptblocks, a harness with no gallery modules | `pwsh` |
| `docker-compose-svc` | A small HTTP service shipped as a container: non-root image with a real HEALTHCHECK, compose file driven by `PORT`, pure-function contract with unit tests that need no Docker, and a smoke test that starts the container, checks every answer and leaves nothing running | `docker`, `make` |
| `jsonnet-config` | A service manifest in Jsonnet with its rules as data: validators that name every problem, a renderer that sorts and sums, and an 18-check suite that proves each rule fires | `jsonnet`, `make` |
| `d-cli` | D compiled with LDC: counting over `ubyte[]`, hand-written argv parser, report building behind an `Io` struct of function pointers, a 37-assertion harness and a parity suite that diffs the output against `wc` | `ldc2`, `make` |
| `sml-cli` | Standard ML compiled with MLton to a single native binary: counting over `Word8Vector`, hand-written argv parser, a 37-assertion SML harness and a parity suite that diffs the output against `wc` | `mlton`, `make` |
| `haxe-cli` | Haxe command line tool compiled to Neko: byte-accurate `wc`-style counting, hand-written option parser, dependency-free Haxe test suite plus a parity suite that diffs the output against `wc` | `haxe`, `neko`, `make` |
| `mdbook-docs` | An mdBook site with a shell link checker wired into CI: relative links and images must exist, every page must be listed in `src/SUMMARY.md`, and 25 assertions prove it catches broken links, missing images and orphan pages | `mdbook`, `make` |

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
