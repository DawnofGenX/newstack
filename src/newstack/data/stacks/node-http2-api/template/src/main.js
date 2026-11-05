import process from "node:process";

import { createServer, listen, stop } from "./server.js";
import { runSelftest } from "./selftest.js";

const DEFAULT_PORT = 5478;

function parsePort(raw, fallback) {
  if (raw === undefined || raw === "") return fallback;
  if (!/^\d+$/.test(raw)) {
    console.error(`PORT must be a number, got ${raw}`);
    process.exit(2);
  }
  const port = Number(raw);
  if (port < 0 || port > 65_535) {
    console.error(`PORT is out of range: ${port}`);
    process.exit(2);
  }
  return port;
}

async function main(argv) {
  if (argv.includes("--selftest")) {
    const checks = await runSelftest();
    console.log(`selftest: ${checks} checks passed`);
    return;
  }

  const host = process.env.HOST || "127.0.0.1";
  const port = parsePort(process.env.PORT, DEFAULT_PORT);
  const { server } = createServer({ log: (line) => console.error(`h2 ${line}`) });
  await listen(server, host, port);
  console.log(`listening on http://${host}:${port} (h2c, prior knowledge)`);

  const drain = (signal) => {
    console.error(`${signal} received: draining`);
    stop(server).then(() => process.exit(0));
  };
  process.on("SIGTERM", () => drain("SIGTERM"));
  process.on("SIGINT", () => drain("SIGINT"));
}

main(process.argv.slice(2)).catch((error) => {
  console.error(`h2 server failed: ${error.message}`);
  process.exit(1);
});
