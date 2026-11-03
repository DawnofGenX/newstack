# {{ title }}

{{ description }}

A [Next.js](https://nextjs.org) app using the App Router, TypeScript, Tailwind CSS 4, and Vitest.

## Getting started

```bash
npm install
npm run dev
```

Open http://localhost:3000 to view the app.

## Scripts

| Command | Description |
| --- | --- |
| `npm run dev` | Start the development server |
| `npm run build` | Create a production build |
| `npm run start` | Serve the production build |
| `npm run lint` | Run ESLint |
| `npm run typecheck` | Type-check with `tsc --noEmit` |
| `npm test` | Run the component tests once with Vitest |

## Checks

```bash
npm run typecheck
npm test
npm run build
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
