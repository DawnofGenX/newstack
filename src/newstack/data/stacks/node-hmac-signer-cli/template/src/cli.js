#!/usr/bin/env node
import { parseArgs } from "node:util";
import { computeSignature, verifySignature } from "./hmac.js";

const { values, positionals } = parseArgs({
  options: {
    secret: { type: "string" },
    payload: { type: "string" },
    timestamp: { type: "string" },
    signature: { type: "string" },
    tolerance: { type: "string" },
  },
  allowPositionals: true,
});

const command = positionals[0] ?? "sign";
const secret = values.secret;
const payload = values.payload ?? "";
const timestamp = values.timestamp
  ? Number(values.timestamp)
  : Math.floor(Date.now() / 1000);

if (command === "--help" || command === "-h" || command === "help") {
  process.stdout.write(
    "Usage: hmac-signer sign|verify --secret <s> --payload <p> [--timestamp N] [--signature v1=...] [--tolerance N]\n",
  );
  process.exit(0);
}

if (command === "sign") {
  process.stdout.write(computeSignature(secret, payload, timestamp) + "\n");
  process.exit(0);
}

if (command === "verify") {
  const tol = values.tolerance ? Number(values.tolerance) : 300;
  const ok = verifySignature(secret, payload, values.signature, timestamp, tol);
  process.stdout.write((ok ? "valid" : "invalid") + "\n");
  process.exit(ok ? 0 : 1);
}

console.error("unknown command");
process.exit(2);
