# {{ title }}

{{ description }}

A [SvelteKit 3](https://svelte.dev/docs/kit) application written in TypeScript, with a
runes-based component, unit tests, and static site generation via `@sveltejs/adapter-static`.

## Requirements

- Node.js {{ node_version }} or newer
- {{ package_manager_prereq }}

## Setup

```sh
{{ package_manager_install }}
```

## Development

```sh
{{ package_manager_run }} dev
```

Then open the printed URL (usually <http://localhost:5173>).

## Type checking

```sh
{{ package_manager_run }} check
```

This runs `svelte-kit sync` followed by `svelte-check` against `tsconfig.json`.

## Tests

```sh
{{ package_manager_test }}
```

Component tests use [Vitest](https://vitest.dev) with `jsdom` and
[`@testing-library/svelte`](https://github.com/testing-library/svelte-testing-library).
Run them in watch mode with `{{ package_manager_run }} test:watch`.

## Build

```sh
{{ package_manager_run }} build
{{ package_manager_run }} preview
```

`{{ package_manager_run }} build` prerenders the app into static HTML in `build/`. Because no server is
required, the whole folder can be served by any static host.

## Project layout

```
src/
  app.html              HTML shell
  lib/Counter.svelte    Svelte 5 component using $state
  lib/Counter.test.ts   Vitest + Testing Library test
  routes/+layout.ts     prerender = true
  routes/+page.svelte   home page
  vitest-setup.ts       Testing Library cleanup between tests
static/                 static assets copied verbatim into build/
vite.config.ts          SvelteKit plugin, adapter-static and Vitest config
```

## License

MIT — see [LICENSE](LICENSE).
