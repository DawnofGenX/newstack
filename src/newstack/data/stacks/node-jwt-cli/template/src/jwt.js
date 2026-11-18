import { createHmac, timingSafeEqual } from "node:crypto";

export function base64url(buf) {
  return Buffer.from(buf).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function base64urlDecode(text) {
  const padded = String(text).replace(/-/g, "+").replace(/_/g, "/");
  return Buffer.from(padded + "=".repeat((4 - (padded.length % 4)) % 4), "base64");
}

function sign(header, payload, secret) {
  const body = `${base64url(JSON.stringify(header))}.${base64url(JSON.stringify(payload))}`;
  return `${body}.${base64url(createHmac("sha256", secret).update(body).digest())}`;
}

// issue builds a signed HS256 token; expiresIn is in seconds.
export function issue(payload, secret, { expiresIn = 3600, now = Date.now() } = {}) {
  if (!secret) throw new Error("secret is required");
  const claims = { ...payload };
  if (expiresIn !== undefined) claims.exp = Math.floor(now / 1000) + expiresIn;
  return sign({ alg: "HS256", typ: "JWT" }, claims, secret);
}

export function decode(token) {
  const parts = String(token).split(".");
  if (parts.length !== 3) throw new Error("token must have three segments");
  return {
    header: JSON.parse(base64urlDecode(parts[0]).toString("utf8")),
    payload: JSON.parse(base64urlDecode(parts[1]).toString("utf8")),
    signature: parts[2],
    signingInput: `${parts[0]}.${parts[1]}`,
  };
}

// verify checks the signature and the exp/nbf claims.
export function verify(token, secret, { now = Date.now(), leeway = 0 } = {}) {
  const { header, payload, signingInput, signature } = decode(token);
  if (header.alg !== "HS256") throw new Error(`unsupported alg: ${header.alg}`);
  const expected = base64url(createHmac("sha256", secret).update(signingInput).digest());
  const a = Buffer.from(expected);
  const b = Buffer.from(signature);
  if (a.length !== b.length || !timingSafeEqual(a, b)) throw new Error("signature mismatch");
  const seconds = Math.floor(now / 1000);
  if (typeof payload.exp === "number" && seconds > payload.exp + leeway) throw new Error("token expired");
  if (typeof payload.nbf === "number" && seconds + leeway < payload.nbf) throw new Error("token not yet valid");
  return { header, payload };
}
