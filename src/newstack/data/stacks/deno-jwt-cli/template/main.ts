import { sign, verify } from "./src/jwt.ts";

const args = Deno.args;
if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
  console.log("usage: jwt-cli sign --secret S [--payload JSON] [--sub X] [--exp SEC]");
  console.log("       jwt-cli verify --secret S <token>");
  Deno.exit(0);
}

function get(flag: string): string | undefined {
  const i = args.indexOf(flag);
  return i >= 0 ? args[i + 1] : undefined;
}

const cmd = args[0];
if (cmd === "sign") {
  const secret = get("--secret") ?? "";
  const payloadJson = get("--payload");
  let payload: Record<string, unknown> = {};
  if (payloadJson) payload = JSON.parse(payloadJson);
  const sub = get("--sub");
  if (sub) payload.sub = sub;
  const exp = get("--exp");
  if (exp) payload.exp = Math.floor(Date.now() / 1000) + Number(exp);
  const token = await sign(payload, secret);
  console.log(token);
  Deno.exit(0);
} else if (cmd === "verify") {
  const secret = get("--secret") ?? "";
  // token is the positional after 'verify'
  let tokenArg = "";
  for (let i = 1; i < args.length; i++) {
    if (args[i] === "--secret") { i++; continue; }
    tokenArg = args[i];
    break;
  }
  const res = await verify(tokenArg, secret);
  if (res === null) {
    console.error("invalid token");
    Deno.exit(1);
  }
  console.log(JSON.stringify(res));
  Deno.exit(0);
} else {
  console.error("unknown command");
  Deno.exit(2);
}