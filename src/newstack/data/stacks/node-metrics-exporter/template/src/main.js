// main.js — process entry: env, selftest mode, signals.

import { createApp } from "./app.js";
import { Registry } from "./metrics.js";
import { runSelftest } from "./selftest.js";
import { createServer, listen, stop } from "./server.js";

const DEFAULT_PORT = 5474;
const DEFAULT_HOST = "127.0.0.1";

function parsePort(raw) {
  if (raw === undefined || raw === "") return DEFAULT_PORT;
  if (!/^\d+$/.test(raw)) throw new Error(`PORT must be a number, got "${raw}"`);
  const port = Number(raw);
  if (port < 1 || port > 65535) throw new Error(`PORT must be 1-65535, got ${port}`);
  return port;
}

if (process.argv.includes("--selftest")) {
  // runSelftest is async (it exercises the app through Request objects), so the
  // exit code has to wait for the promise or a failing check exits 0.
  const checks = await runSelftest();
  console.log(`selftest: ${checks} checks passed`);
  process.exit(0);
}

let port;
try {
  port = parsePort(process.env.PORT);
} catch (error) {
  process.stderr.write(`main: ${error.message}\n`);
  process.exit(2);
}
const host = process.env.HOST || DEFAULT_HOST;

const registry = new Registry();
const app = createApp({ registry });
const server = createServer(app);
await listen(server, host, port);
process.stdout.write(`listening http://${host}:${port}\n`);

let closing = false;
for (const signal of ["SIGTERM", "SIGINT"]) {
  process.on(signal, () => {
    if (closing) return;
    closing = true;
    process.stdout.write(`${signal} received: draining\n`);
    stop(server).then(() => process.exit(0));
  });
}
