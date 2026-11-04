# {{ title }}

{{ description }}

Vue 3 + Vite + TypeScript single page application, scaffolded by
[newstack](https://github.com/DawnofGenX/newstack). Unit tests run on
[Vitest](https://vitest.dev) with [@vue/test-utils](https://test-utils.vuejs.org).

## Requirements

- Node.js {{ node_version }} or newer
- {{ package_manager_prereq }}

## Getting started

```bash
{{ package_manager_install }}
{{ package_manager_run }} dev
```

Vite serves the app on <http://localhost:5173> with hot module replacement.

## Scripts

| Command | What it does |
| --- | --- |
| `{{ package_manager_run }} dev` | Start the Vite dev server with HMR |
| `{{ package_manager_run }} typecheck` | Type-check the app with `vue-tsc --noEmit` |
| `{{ package_manager_test }}` | Run the Vitest unit tests once |
| `{{ package_manager_run }} build` | Type-check and build for production into `dist/` |
| `{{ package_manager_run }} preview` | Serve the production build locally |

## Project layout

```
src/
  main.ts               app entry point
  App.vue               root component
  components/
    Counter.vue         example component (Composition API + <script setup>)
    Counter.test.ts     Vitest + @vue/test-utils unit test
```

## Testing

Tests live next to the code as `*.test.ts` and run in a jsdom environment
configured in `vite.config.ts`. Run them once with `{{ package_manager_test }}`, or in watch
mode with `npx vitest`.

## Continuous integration

`.github/workflows/ci.yml` installs dependencies, type-checks, tests and builds
on Node.js {{ node_list }} for every push to `main` and every pull request. It uses
`{{ package_manager_install }}` (not the lockfile-strict `{{ package_manager_ci }}`) so it
works in a fresh project with no lockfile committed yet. Commit
`{{ package_manager_lock }}` once you have generated it to get reproducible CI installs.

## License

MIT — see [LICENSE](./LICENSE).
