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
newstack adopt ~/code/old-project --dry-run    # retrofit CI/lint onto existing code
newstack update ~/code/app --dry-run   # re-apply template changes, keep your edits
newstack outdated ~/code/app         # what has the template moved on from?
newstack check --all                # prove every stack on this machine
newstack doctor                     # which toolchains do I have?
```

Every command takes `--json` where it makes sense, so the tool is scriptable.

`newstack new` renders variables, initialises git with a first commit, and (with
`--github`) creates the remote repository and pushes — one command from empty
directory to CI-ready project.

## Stacks

| Stack | What you get | Toolchain |
| --- | --- | --- |
| `python-lib` | src layout, hatchling build, pytest, ruff, 4-version CI matrix | `uv` |
| `python-cli` | console entry point on argparse, zero runtime deps, tested CLI | `uv` |
| `fastapi` | typed JSON API, pydantic models, TestClient tests, Dockerfile | `uv` |
| `django` | Django 6.1 app: config/core split, SQLite, pytest-django, migration drift check | `uv` |
| `flask` | Flask app factory: JSON routes, pytest fixtures, ruff, CI | `uv` |
| `react-vite-ts` | React 19 + Vite + TS, Vitest + Testing Library, typecheck + build | `node`, `npm` |
| `vue-vite-ts` | Vue 3 + Vite + TS, Vitest + @vue/test-utils, typecheck + build | `node`, `npm` |
| `next-app-ts` | Next.js App Router + TS + Tailwind 4, Vitest + Testing Library | `node`, `npm` |
| `chrome-extension` | MV3 extension: popup + service worker + content script, `npm run pack` → extension.zip | `node`, `npm` |
| `astro` | Astro + TS content site: typed frontmatter, Vitest unit tests, `astro check` + static build | `node`, `npm` |
| `data-science` | pandas workspace: testable DataFrame helpers, pytest, sample notebook | `uv` |
| `node-express-ts` | Express 5 API, typed handlers, supertest tests | `node`, `npm` |
| `svelte-kit-ts` | SvelteKit + TS, Svelte 5 runes component, Vitest, static adapter build | `node`, `npm` |
| `go-cli` | stdlib-only Go CLI: `flag` parsing, table tests, vet/test/build gates | `go` |
| `go-http` | Go HTTP service on `net/http`: JSON routes, `httptest` suite, graceful shutdown | `go` |
| `rust-cli` | std-only Rust CLI: lib+bin split, fmt/clippy/test/release-build gates | `cargo` |
| `rust-axum` | axum service: typed routes, shared state, `tower` oneshot tests, fmt/clippy | `cargo` |
| `cpp-cmake-cli` | C++20 CLI: CMake lib+bin split, CTest suite, warning-clean GCC/Clang build | `cmake`, `g++` |
| `terraform-module` | Reusable module: validated inputs, computed tags, `terraform test` cases incl. a rejected input | `terraform` |
| `ruby-sinatra` | Sinatra JSON API: modular app, RSpec + rack-test suite, RuboCop, committed lockfile | `ruby`, `bundle` |
| `java-maven-cli` | Java 21 CLI on Maven: pure counting logic, 21 JUnit 5 tests, runnable jar | `java`, `mvn` |
| `spring-boot` | Java 21 Spring Boot 3 web service on Maven: a wc-style `/stats` endpoint, a pure service, and a JUnit 5 + MockMvc suite | `java`, `mvn` |
| `php-composer-cli` | PHP 8.3 CLI on Composer: PSR-4 autoloading, a PHPUnit 11 suite, and a wc-style text counter | `php`, `composer` |
| `symfony-app` | Symfony 7 web app on PHP 8.3: a JSON route wired to a pure service, kernel-level PHPUnit test, working `bin/console` | `php`, `composer` |
| `csharp-cli` | C# 12 CLI on .NET 8: pure counting library, xUnit suite, exit codes as a contract | `dotnet` |
| `dotnet-cli` | .NET 8 C# CLI with a solution file: counting core, hand-written argv parser, xUnit suite, exit codes as a contract | `dotnet` |
| `elixir-mix-cli` | Elixir CLI on Mix: pure counting module, ExUnit suite, escript binary | `elixir`, `mix` |
| `dart-cli` | Dart 3 CLI: pub package with a pure counting library, package:test suite and zero runtime dependencies | `dart` |
| `kotlin-cli` | Kotlin CLI on Maven (no Gradle wrapper to ship): pure counting core, JUnit 5 suite, shaded runnable jar | `java`, `mvn` |
| `zig-cli` | Zig 0.17 CLI: counting module with in-source test blocks, `zig build test`, no runtime | `zig` |
| `julia-cli` | Julia CLI: pure counting module, `Test` stdlib suite, zero external packages | `julia` |
| `nim-cli` | Nim CLI: pure counting module, `unittest` suite that also checks exit codes, `nimble build` binary | `nim`, `nimble` |
| `perl-cli` | Perl CLI on core modules only: `Makefile.PL` + `Test::More` suite, no CPAN install step | `perl`, `make` |
| `lua-cli` | Lua 5.4 CLI: stdlib-only modules, a hand-rolled spec harness, zero luarocks dependencies | `lua5.4` |
| `fsharp-cli` | F# on .NET 8: pure counting core, `Mode` discriminated union parser, xUnit suite that launches the binary for its exit codes | `dotnet` |
| `crystal-cli` | Crystal CLI: stdlib-only modules, `crystal spec` suite, compiled binary with a 0/2/1 exit contract | `crystal` |
| `bun-cli` | Bun CLI: pure counting module, hand-written option parser, zero-dependency `bun:test` suite | `bun` |
| `r-cli` | R CLI on base R only: pure counting function, hand-written option parser, dependency-free test harness | `Rscript` |
| `ocaml-cli` | OCaml CLI on dune: pure counting library, hand-written option parser, stdlib-only test harness, zero opam dependencies | `ocaml`, `dune` |
| `static-site` | HTML/CSS/JS page, `node:test` suite, GitHub Pages deploy workflow | `node` |
| `helm-chart` | Kubernetes Helm chart: schema-validated values, named templates, hardened Deployment/Service, lint+render checks with no cluster | `helm` |
| `gleam-cli` | Gleam CLI: pure counting module, hand-written option parser, stdlib-only test harness, Erlang helper for argv/stdin/exit codes | `gleam` |
| `scala-cli` | Scala 3 CLI built with scala-cli (no sbt): pure counting core, hand-rolled argv parser, munit suites, wrapper that returns the process exit code | `scala-cli`, `java` |
| `haskell-cli` | Haskell CLI on GHC and cabal: pure counting core, hand-rolled argv parser, dependency-free test harness, I/O behind a record | `ghc`, `cabal` |
| `clojure-cli` | Clojure CLI on `deps.edn` (no Leiningen): pure counting core, hand-rolled argv parser, `clojure.test` suites, I/O behind a record | `clojure`, `java` |

Each generated project ships its own `.github/workflows/` that is ready to run, plus a
README, an MIT licence, a `.gitignore`, and a `.newstack.json` record that `newstack
update` uses to re-apply later template changes.

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
- **Updates are a hash comparison, not a diff dance.** `.newstack.json` records what
  newstack wrote; a file counts as yours only once it stops matching that hash, so
  `update` never has to guess whose change it is looking at.

## Roadmap

- More stacks: Swift.
- `--license apache-2.0|bsd-3` and other variable choices beyond the current defaults.

## Licence

MIT — see [LICENSE](LICENSE).
