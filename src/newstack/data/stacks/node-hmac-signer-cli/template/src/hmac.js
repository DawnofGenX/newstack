import { createHmac, timingSafeEqual } from "node:crypto";

export function computeSignature(secret, payload, timestamp) {
  const ts = timestamp ?? Math.floor(Date.now() / 1000);
  const hmac = createHmac("sha256", secret)
    .update(`${ts}.${payload}`)
    .digest("hex");
  return `v1=${hmac}`;
}

export function verifySignature(
  secret,
  payload,
  signature,
  timestamp,
  tolerance = 300,
  now = Date.now(),
) {
  if (typeof signature !== "string" || !signature.startsWith("v1=")) return false;
  const ts = Number(timestamp);
  if (!Number.isFinite(ts)) return false;
  const expected = computeSignature(secret, payload, ts);
  const a = Buffer.from(signature, "utf8");
  const b = Buffer.from(expected, "utf8");
  if (a.length !== b.length) return false;
  if (!timingSafeEqual(a, b)) return false;
  const nowSec = Math.floor(now / 1000);
  if (Math.abs(nowSec - ts) > tolerance) return false;
  return true;
}
