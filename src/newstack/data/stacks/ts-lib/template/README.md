# {{ title }}

{{ description }}

A publishable TypeScript package: `countText` and `formatCounts`, built by tsup into
ESM (`dist/index.js`) and CJS (`dist/index.cjs`) with declaration files, tested with
vitest, and checked against npm's own rules with publint before you publish.

The point of this scaffold is the part most libraries get wrong — the *published shape*.
`package.json` declares `main`, `module`, `types` and a conditional `exports` map, and CI
proves all of them resolve by importing the built files, then runs `publint` and
`npm pack --dry-run` so a broken entry point fails here rather than in a user's build.

This scaffold asks for **Node {{ node_version }} or newer** (`engines` in `package.json`)
and its CI runs every major in the same list.

## Develop

```bash
{{ package_manager_install }}
{{ package_manager_run }} test        # vitest run
{{ package_manager_run }} typecheck   # tsc --noEmit
```

## Build and publish

```bash
{{ package_manager_run }} build        # tsup → dist/*.js, dist/*.cjs, dist/*.d.ts
node scripts/smoke.mjs                 # both entries import and agree
{{ package_manager_run }} lint:publish # publint: "main"/"types"/"exports" are real
npm pack --dry-run                     # exactly what would be uploaded
```

`prepublishOnly` runs typecheck, test, build and publint, so `npm publish` cannot ship a
package whose declared entry points are missing.

## Layout

- `src/count.ts` — `countText(text: string): Counts` (lines, words, UTF-8 bytes) and
  `sumCounts(...items)`; throws `TypeError` on a non-string instead of coercing.
- `src/format.ts` — `formatCounts(counts, options)`, wc's padded columns plus an optional
  label; `columns` and `width` are options, not globals.
- `src/index.ts` — the public surface; nothing else is exported.
- `tsup.config.ts` — ESM + CJS + d.ts, `target: es2022`, `clean: true`.
- `scripts/smoke.mjs` — imports `dist/index.js` and `require`s `dist/index.cjs`, asserting
  they return the same thing. It fails if either format drifts.

After the first `{{ package_manager_install }}`, commit `{{ package_manager_lock }}` and switch
CI's install step to `{{ package_manager_ci }}` for reproducible installs.

Generated with [newstack](https://github.com/DawnofGenX/newstack).
