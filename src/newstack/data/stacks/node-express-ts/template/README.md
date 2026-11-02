# {{ title }}

{{ description }}

Express 5 on TypeScript: `GET /health`, `GET /items`, `POST /items`.

## Develop

```bash
npm install
npm run dev     # http://localhost:3000
```

## Check

```bash
npm run typecheck
npm test
```

After the first `npm install`, commit `package-lock.json` and switch CI's install step
to `npm ci` for reproducible installs.

Generated with [newstack](https://github.com/DawnofGenX/newstack).
