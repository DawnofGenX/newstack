# {{ title }}

{{ description }}

A static site built with Astro and TypeScript: one page, one layout component, and a
Vitest unit test around the helper the page imports.

Astro 7 refuses to run on an older Node than the one it declares, and that floor moves:
this scaffold asks for **Node {{ node_version }} or newer** (`engines` in `package.json`) and
its CI runs every major in the same list.

## Develop

```bash
{{ package_manager_install }}
{{ package_manager_run }} dev      # http://localhost:4321
```

## Check

```bash
{{ package_manager_run }} typecheck   # astro check (@astrojs/check + typescript)
{{ package_manager_test }}            # vitest run
{{ package_manager_run }} build       # static output in dist/
{{ package_manager_run }} preview     # serve dist/ locally
```

## Layout

- `src/pages/index.astro` — the landing page; its list comes from a typed `Feature[]`.
- `src/layouts/BaseLayout.astro` — document shell and global styles.
- `src/lib/content.ts` — plain TypeScript helper, covered by `src/lib/content.test.ts`.

After the first `{{ package_manager_install }}`, commit `{{ package_manager_lock }}` and switch
CI's install step to `{{ package_manager_ci }}` for reproducible installs.

Generated with [newstack](https://github.com/DawnofGenX/newstack).
