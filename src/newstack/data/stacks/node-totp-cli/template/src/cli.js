#!/usr/bin/env node
import { parseArgs } from "node:util";
import { totp, verify, base32Decode } from "./totp.js";

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    secret: { type: "string" },
    time: { type: "string" },
    digits: { type: "string" },
    algo: { type: "string" },
    base32: { type: "boolean", default: true },
    code: { type: "string" },
    window: { type: "string" },
  },
});

const cmd = positionals[0] ?? "generate";
const secret = values.secret ?? positionals[1];
const time = values.time ? Number(values.time) : Math.floor(Date.now() / 1000);
const opts = {
  digits: values.digits ? Number(values.digits) : 6,
  algo: values.algo ?? "sha1",
  base32: values.base32,
};

if (cmd === "generate" || cmd === "gen") {
  process.stdout.write(totp(secret, time, opts) + "\n");
} else if (cmd === "verify") {
  const ok = verify(secret, values.code, time, {
    ...opts,
    window: values.window ? Number(values.window) : 1,
  });
  process.stdout.write((ok ? "valid" : "invalid") + "\n");
  process.exit(ok ? 0 : 1);
} else {
  console.error("usage: totp-cli generate|verify --secret <s> [--time N] [--digits N]");
  process.exit(2);
}