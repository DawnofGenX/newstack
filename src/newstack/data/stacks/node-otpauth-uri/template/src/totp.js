import { createHmac } from "node:crypto";

const ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";

export function base32Decode(input) {
  const clean = String(input).toUpperCase().replace(/=+$/, "").replace(/\s+/g, "");
  if (!/^[A-Z2-7]*$/.test(clean)) throw new Error("invalid base32 secret");
  let bits = 0;
  let value = 0;
  const out = [];
  for (const ch of clean) {
    value = (value << 5) | ALPHABET.indexOf(ch);
    bits += 5;
    if (bits >= 8) {
      bits -= 8;
      out.push((value >>> bits) & 0xff);
    }
  }
  return Buffer.from(out);
}

export function base32Encode(buf) {
  let bits = 0;
  let value = 0;
  let out = "";
  for (const byte of buf) {
    value = (value << 8) | byte;
    bits += 8;
    while (bits >= 5) {
      bits -= 5;
      out += ALPHABET[(value >>> bits) & 31];
    }
  }
  if (bits > 0) out += ALPHABET[(value << (5 - bits)) & 31];
  return out;
}

export function hotp(secret, counter, digits = 6) {
  const key = base32Decode(secret);
  const buf = Buffer.alloc(8);
  buf.writeBigUInt64BE(BigInt(counter));
  const mac = createHmac("sha1", key).update(buf).digest();
  const offset = mac[mac.length - 1] & 0x0f;
  const code =
    ((mac[offset] & 0x7f) << 24) |
    ((mac[offset + 1] & 0xff) << 16) |
    ((mac[offset + 2] & 0xff) << 8) |
    (mac[offset + 3] & 0xff);
  return String(code % 10 ** digits).padStart(digits, "0");
}

export function totp(secret, { time = Date.now(), step = 30, digits = 6 } = {}) {
  const counter = Math.floor(time / 1000 / step);
  return hotp(secret, counter, digits);
}

export function otpauthUri({ secret, issuer, account, digits = 6, period = 30, algorithm = "SHA1" }) {
  if (!secret) throw new Error("secret is required");
  if (!account) throw new Error("account is required");
  const label = issuer ? `${encodeURIComponent(issuer)}:${encodeURIComponent(account)}` : encodeURIComponent(account);
  const params = new URLSearchParams({ secret: String(secret).toUpperCase() });
  if (issuer) params.set("issuer", issuer);
  params.set("algorithm", algorithm);
  params.set("digits", String(digits));
  params.set("period", String(period));
  return `otpauth://totp/${label}?${params.toString()}`;
}

export function parseOtpauthUri(uri) {
  const url = new URL(String(uri));
  if (url.protocol !== "otpauth:") throw new Error("not an otpauth uri");
  if (url.host !== "totp") throw new Error(`unsupported type: ${url.host}`);
  const label = decodeURIComponent(url.pathname.replace(/^\//, ""));
  const [labelIssuer, ...rest] = label.split(":");
  const account = rest.length ? rest.join(":") : labelIssuer;
  const params = url.searchParams;
  return {
    secret: (params.get("secret") ?? "").toUpperCase(),
    issuer: params.get("issuer") ?? (rest.length ? labelIssuer : ""),
    account,
    digits: Number(params.get("digits") ?? 6),
    period: Number(params.get("period") ?? 30),
    algorithm: params.get("algorithm") ?? "SHA1",
  };
}
