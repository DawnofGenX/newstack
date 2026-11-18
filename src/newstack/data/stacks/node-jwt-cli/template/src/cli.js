#!/usr/bin/env node
import { parseArgs } from "node:util";
import { issue, verify, decode } from "./jwt.js";

const [, , command, ...rest] = process.argv;
const { values, positionals } = parseArgs({
  args: rest,
  options: {
    secret: { type: "string" },
    payload: { type: "string" },
    ttl: { type: "string" },
    leeway: { type: "string" },
    now: { type: "string" },
  },
  allowPositionals: true,
});

const secret = values.secret ?? process.env.JWT_SECRET;
const now = values.now !== undefined ? Number(values.now) * 1000 : Date.now();

try {
  if (command === "sign") {
    const payload = values.payload ? JSON.parse(values.payload) : {};
    const ttl = values.ttl !== undefined ? Number(values.ttl) : 3600;
    process.stdout.write(issue(payload, secret, { expiresIn: ttl, now }) + "\n");
  } else if (command === "verify") {
    const token = positionals[0];
    if (!token) throw new Error("verify needs a token argument");
    const { payload } = verify(token, secret, { now, leeway: Number(values.leeway ?? 0) });
    process.stdout.write(JSON.stringify(payload) + "\n");
  } else if (command === "decode") {
    const token = positionals[0];
    if (!token) throw new Error("decode needs a token argument");
    process.stdout.write(JSON.stringify(decode(token), null, 2) + "\n");
  } else {
    process.stderr.write("usage: cli.js <sign|verify|decode> [options]\n");
    process.exit(2);
  }
} catch (err) {
  process.stderr.write(`error: ${err.message}\n`);
  process.exit(1);
}
