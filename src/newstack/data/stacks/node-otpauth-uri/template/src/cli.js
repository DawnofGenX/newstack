#!/usr/bin/env node
import { parseArgs } from "node:util";
import { otpauthUri, parseOtpauthUri, totp, hotp } from "./totp.js";

const [, , command, ...rest] = process.argv;
const { values } = parseArgs({
  args: rest,
  options: {
    secret: { type: "string" },
    issuer: { type: "string" },
    account: { type: "string" },
    digits: { type: "string" },
    period: { type: "string" },
    time: { type: "string" },
    counter: { type: "string" },
  },
  allowPositionals: true,
});

try {
  if (command === "uri") {
    process.stdout.write(
      otpauthUri({
        secret: values.secret,
        issuer: values.issuer,
        account: values.account,
        digits: Number(values.digits ?? 6),
        period: Number(values.period ?? 30),
      }) + "\n"
    );
  } else if (command === "code") {
    if (values.counter !== undefined) {
      process.stdout.write(hotp(values.secret, Number(values.counter), Number(values.digits ?? 6)) + "\n");
    } else {
      const time = values.time !== undefined ? Number(values.time) * 1000 : Date.now();
      process.stdout.write(
        totp(values.secret, { time, step: Number(values.period ?? 30), digits: Number(values.digits ?? 6) }) + "\n"
      );
    }
  } else if (command === "parse") {
    process.stdout.write(JSON.stringify(parseOtpauthUri(rest[0]), null, 2) + "\n");
  } else {
    process.stderr.write("usage: cli.js <uri|code|parse> [options]\n");
    process.exit(2);
  }
} catch (err) {
  process.stderr.write(`error: ${err.message}\n`);
  process.exit(1);
}
