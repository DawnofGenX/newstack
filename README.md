# newstack

[![CI](https://github.com/DawnofGenX/newstack/actions/workflows/ci.yml/badge.svg)](https://github.com/DawnofGenX/newstack/actions/workflows/ci.yml)
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

Not on PyPI yet — install straight from the repository:

```bash
uv tool install git+https://github.com/DawnofGenX/newstack
# or, without installing:
uvx --from git+https://github.com/DawnofGenX/newstack newstack list
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
| `react-vite-ts` | React 19 + Vite + TS, Vitest + Testing Library, typecheck + build | `node`, `npm` |
| `node-express-ts` | Express 5 API, typed handlers, supertest tests | `node`, `npm` |
| `static-site` | HTML/CSS/JS page with a GitHub Pages deploy workflow | `node` |

Each generated project ships its own `.github/workflows/` that is ready to run, plus a
README, an MIT licence and a `.gitignore`.

## The green guarantee

A template is only as good as its last successful run, so `newstack` treats
verification as a first-class command:

```console
$ newstack check --all
  fastapi          PASS    1.0s  3 step(s)
  node-express-ts  PASS    2.2s  3 step(s)
  python-cli       PASS    0.5s  4 step(s)
  python-lib       PASS    0.4s  3 step(s)
  react-vite-ts    PASS    3.2s  4 step(s)
  static-site      PASS    0.1s  3 step(s)
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

A stack is a directory with a manifest and a template tree:

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
  ]
}
```

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
- More stacks: Go service, Rust CLI, Django, Vue, SvelteKit.
- `--license apache-2.0|bsd-3` and other variable choices beyond the current defaults.

## Licence

MIT — see [LICENSE](LICENSE).
