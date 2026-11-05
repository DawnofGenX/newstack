// Entry point: workdir from UPLOAD_DIR, address from HOST/PORT.
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import { UploadStore } from "./store.js";
import { createServer, listen, stop } from "./server.js";

function parsePort(raw) {
  const port = Number(raw);
  if (!/^\d+$/.test(String(raw)) || port < 1 || port > 65535) {
    throw new Error(`bad PORT ${JSON.stringify(raw)}`);
  }
  return port;
}

async function main() {
  const host = process.env.HOST || "127.0.0.1";
  let port;
  try {
    port = parsePort(process.env.PORT ?? "8080");
  } catch (error) {
    console.error(`blog-count: ${error.message}`);
    process.exit(2);
  }

  const root = process.env.UPLOAD_DIR || (await mkdtemp(path.join(os.tmpdir(), "uploads-")));
  const store = await UploadStore.open(root);
  const server = await createServer(store);
  const bound = await listen(server, host, port);
  console.log(`listening on ${host}:${bound} (${store.count()} uploads in ${root})`);

  let stopping = false;
  const shutdown = async (signal) => {
    if (stopping) return;
    stopping = true;
    console.log(`${signal} received: stopping`);
    await stop(server);
    process.exit(0);
  };
  process.on("SIGTERM", () => shutdown("SIGTERM"));
  process.on("SIGINT", () => shutdown("SIGINT"));

  if (process.env.UPLOAD_DIR === undefined) {
    process.on("exit", () => {
      rm(root, { recursive: true, force: true }).catch(() => {});
    });
  }
}

main().catch((error) => {
  console.error(`blog-count: ${error.message}`);
  process.exit(1);
});
