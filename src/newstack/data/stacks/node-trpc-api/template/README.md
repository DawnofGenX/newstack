# {{ npm_name }}

A tRPC v11 JSON API with a direct server-side caller test and an HTTP smoke check.

```bash
npm install
npm run typecheck
npm test
npm run build
PORT=5511 npm start
bash smoke.sh
```
