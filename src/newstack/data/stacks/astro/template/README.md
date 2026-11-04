# {{ title }}

{{ description }}

A static site built with Astro and TypeScript: one page, one layout component, and a
Vitest unit test around the helper the page imports.

Astro 7 refuses to run on an older Node than the one it declares, and that floor moves:
this scaffold asks for **Node 22.23.4 or newer** (`engines` in `package.json`) and its CI
runs Node 24.

## Develop

```bash
npm install
npm run dev      # http://localhost:4321
```

## Check

```bash
npm run typecheck   # astro check (@astrojs/check + typescript)
npm test            # vitest run
npm run build       # static output in dist/
npm run preview     # serve dist/ locally
```

## Layout

- `src/pages/index.astro` — the landing page; its list comes from a typed `Feature[]`.
- `src/layouts/BaseLayout.astro` — document shell and global styles.
- `src/lib/content.ts` — plain TypeScript helper, covered by `src/lib/content.test.ts`.

After the first `npm install`, commit `package-lock.json` and switch CI's install step
to `npm ci` for reproducible installs.

Generated with [newstack](https://github.com/DawnofGenX/newstack).
