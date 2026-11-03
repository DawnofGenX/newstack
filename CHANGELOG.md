# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-11-03

### Added

- Three new stacks, each with `detect` + `adopt` metadata like the rest of the registry:
  - `flask` — app factory + blueprint, JSON routes, pytest fixtures, ruff with a pinned
    rule set.
  - `vue-vite-ts` — Vue 3 + Vite + TypeScript from `create-vue`, Vitest +
    `@vue/test-utils`, real typecheck (`vue-tsc -p tsconfig.app.json`; plain `--noEmit`
    on a solution-style root would check nothing).
  - `next-app-ts` — Next 16 App Router + TypeScript + Tailwind 4 from
    `create-next-app`, with the Vitest + Testing Library test and `tsc --noEmit`
    scripts that the generator does not provide.
- CI matrix grows to thirteen stack jobs; each new stack's own workflow was also proven
  green in a throwaway repository.

### Changed

- Node stacks install with `npm install --no-audit --no-fund` again — `--silent` was
  hiding npm's error output, so a failed install reported an empty reason.
- `vue-vite-ts` pins `vitest ^5.1.0`: with `^4.x`, npm 10 (Node 22, the CI runner)
  crashes inside arborist's peer resolution with `Cannot read properties of null
  (reading 'edgesOut')`, while npm 11 resolves it fine.

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
