# {{ title }}

{{ description }}

React 19 + TypeScript on Vite, tested with Vitest and Testing Library.

## Develop

```bash
npm install
npm run dev      # http://localhost:5173
```

## Check

```bash
npm run typecheck   # tsc --noEmit
npm test            # vitest run
npm run build       # production bundle in dist/
```

After the first `npm install`, commit `package-lock.json` and switch CI's install step
to `npm ci` for reproducible installs.

Generated with [newstack](https://github.com/DawnofGenX/newstack).
