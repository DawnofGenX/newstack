#!/usr/bin/env node
/** Entry point: serve, or run the offline checks with --selftest. */
import { createApp } from "./app.js";
import { runSelftest } from "./selftest.js";

const DEFAULT_PORT = 8080;
const DEFAULT_HOST = "127.0.0.1";

export function parsePort(raw: string | undefined): number {
  if (raw === undefined || raw === "") return DEFAULT_PORT;
  const port = Number.parseInt(raw, 10);
  if (!Number.isInteger(port) || port < 1 || port > 65535 || String(port) !== raw.trim()) {
    process.stderr.write(`invalid PORT: ${raw}\n`);
    process.exit(2);
  }
  return port;
}

async function main(argv: string[]): Promise<void> {
  if (argv.includes("--selftest")) {
    process.exit(runSelftest());
  }

  const port = parsePort(process.env["PORT"]);
  const host = process.env["HOST"] ?? DEFAULT_HOST;
  const app = createApp();

  const close = async (signal: string) => {
    process.stderr.write(`received ${signal}: closing\n`);
    await app.close();
    process.exit(0);
  };
  for (const signal of ["SIGINT", "SIGTERM"] as const) {
    process.on(signal, () => {
      void close(signal);
    });
  }

  await app.listen({ port, host });
  process.stdout.write(`listening on http://${host}:${port}\n`);
}

void main(process.argv.slice(2));
