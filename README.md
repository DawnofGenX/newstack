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
| `static-site` | HTML/CSS/JS page, `node:test` suite, GitHub Pages deploy workflow | `node` |

Each generated project ships its own `.github/workflows/` that is ready to run, plus a
README, an MIT licence and a `.gitignore`.

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
| Template updates after generation | no (roadmap) | no | **yes** (`copier update`) | no | no | no |
| Creates the git repo + remote | **yes** (`--github`) | no | via hooks | no | no | yes |

Pick `copier` if you need `copier update` three-way merges against a single template you
own. Pick `newstack` when you want the same standard applied across several languages
without maintaining one template per stack.

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

## Roadmap

- `newstack update` — re-apply upstream template changes to an existing project.
- More stacks: Vue, Next.js, Flask.
- `--license apache-2.0|bsd-3` and other variable choices beyond the current defaults.

## Licence

MIT — see [LICENSE](LICENSE).
