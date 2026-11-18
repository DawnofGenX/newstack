import http from 'node:http';
import { URL } from 'node:url';
import { FLAGS, resolveFlags } from './flags.js';

export function createServer(flags = FLAGS) {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    if (url.pathname === '/flags') {
      const user = url.searchParams.get('user') || 'anonymous';
      const resolved = resolveFlags(flags, user);
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ user, flags: resolved }));
      return;
    }
    if (url.pathname === '/health') {
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ ok: true }));
      return;
    }
    res.statusCode = 404;
    res.end('not found');
  });
  return server;
}

export function start(port = Number(process.env.PORT) || 3000) {
  const server = createServer();
  server.listen(port, () => {
    console.log(`listening on ${port}`);
  });
  const shutdown = () => {
    server.close(() => process.exit(0));
  };
  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);
  return server;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  // allow `node src/server.js`
  start();
}
