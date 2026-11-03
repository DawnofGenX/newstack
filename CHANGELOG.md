# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-11-03

### Added

- **Sixteen new stacks**, every one shipped with `detect` + `adopt` metadata so
  `newstack adopt` recognises it too. The registry is at 26 stacks.
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
