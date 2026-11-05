// main.js — process entry: env parsing, migrations, Bun.serve, signals,
// and the offline --selftest mode (no socket bound).
import { openDb, migrate } from "./db.js";
import { buildRoutes } from "./app.js";
import { runSelftest } from "./selftest.js";

if (process.argv.includes("--selftest")) {
  const { checks, label } = runSelftest();
  console.log(`selftest: ${checks} checks passed`);
  if (label) console.log(label);
  process.exit(0);
}

const DEFAULT_PORT = 5471;
const DEFAULT_HOST = "127.0.0.1";

function resolvePort() {
  const raw = process.env.PORT;
  if (raw === undefined || raw === "") return DEFAULT_PORT;
  if (!/^\d+$/.test(raw) || Number(raw) < 1 || Number(raw) > 65535) {
    process.stderr.write(`main: invalid PORT "${raw}" (expected 1-65535)\n`);
    process.exit(2);
  }
  return Number(raw);
}

const port = resolvePort();
const host = process.env.HOST || DEFAULT_HOST;
const dbPath = process.env.DB_PATH || "./notes.db";

const db = openDb(dbPath);
migrate(db); // idempotent, transactional; second boot is a no-op

const { routes, fallback } = buildRoutes(db);
const server = Bun.serve({ hostname: host, port, routes, fetch: fallback });
process.stdout.write(`listening http://${host}:${server.port} db=${dbPath}\n`);

let closing = false;
function shutdown(signal) {
  if (closing) return;
  closing = true;
  server.stop(true); // abort in-flight requests
  db.close();
  process.exit(0);
}
process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
