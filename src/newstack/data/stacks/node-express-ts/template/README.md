# {{ title }}

{{ description }}

Express 5 on TypeScript: `GET /health`, `GET /items`, `POST /items`.

## Develop

```bash
{{ package_manager_install }}
{{ package_manager_run }} dev     # http://localhost:3000
```

## Check

```bash
{{ package_manager_run }} typecheck
{{ package_manager_test }}
```

After the first `{{ package_manager_install }}`, commit `{{ package_manager_lock }}` and switch
CI's install step to `{{ package_manager_ci }}` for reproducible installs.

Generated with [newstack](https://github.com/DawnofGenX/newstack).
