# {{ title }}

{{ description }}

React 19 + TypeScript on Vite, tested with Vitest and Testing Library.

## Develop

```bash
{{ package_manager_install }}
{{ package_manager_run }} dev      # http://localhost:5173
```

## Check

```bash
{{ package_manager_run }} typecheck   # tsc --noEmit
{{ package_manager_test }}            # vitest run
{{ package_manager_run }} build       # production bundle in dist/
```

After the first `{{ package_manager_install }}`, commit `{{ package_manager_lock }}` and
switch CI's install step to `{{ package_manager_ci }}` for reproducible installs.

Generated with [newstack](https://github.com/DawnofGenX/newstack).
