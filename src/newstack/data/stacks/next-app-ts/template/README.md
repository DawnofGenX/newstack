# {{ title }}

{{ description }}

A [Next.js](https://nextjs.org) app using the App Router, TypeScript, Tailwind CSS 4, and Vitest.

## Getting started

```bash
{{ package_manager_install }}
{{ package_manager_run }} dev
```

Open http://localhost:3000 to view the app.

## Scripts

| Command | Description |
| --- | --- |
| `{{ package_manager_run }} dev` | Start the development server |
| `{{ package_manager_run }} build` | Create a production build |
| `{{ package_manager_run }} start` | Serve the production build |
| `{{ package_manager_run }} lint` | Run ESLint |
| `{{ package_manager_run }} typecheck` | Type-check with `tsc --noEmit` |
| `{{ package_manager_test }}` | Run the component tests once with Vitest |

## Checks

```bash
{{ package_manager_run }} typecheck
{{ package_manager_test }}
{{ package_manager_run }} build
```

## Layout

```
app/
  layout.tsx      root layout and metadata
  page.tsx        home page
  counter.tsx     client component with useState
  page.test.tsx   component tests (Vitest + Testing Library)
  globals.css     Tailwind CSS entry point
public/           static assets
```

## License

MIT
