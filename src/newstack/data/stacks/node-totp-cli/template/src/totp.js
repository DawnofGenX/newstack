import { createHmac } from "node:crypto";

const BASE32_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";

export function base32Decode(input) {
  const clean = String(input).replace(/=+$/g, "").replace(/\s+/g, "").toUpperCase();
  let bits = 0;
  let value = 0;
  const bytes = [];
  for (const ch of clean) {
    const idx = BASE32_ALPHABET.indexOf(ch);
    if (idx < 0) throw new Error(`invalid base32 char: ${ch}`);
    value = (value << 5) | idx;
    bits += 5;
    if (bits >= 8) {
      bits -= 8;
      bytes.push((value >>> bits) & 0xff);
    }
  }
  return Buffer.from(bytes);
}

function keyBuffer(secret, base32) {
  if (Buffer.isBuffer(secret)) return secret;
  if (base32) return base32Decode(secret);
  return Buffer.from(String(secret), "utf8");
}

export function hotp(secret, counter, opts = {}) {
  const digits = opts.digits ?? 6;
  const algo = opts.algo ?? "sha1";
  const base32 = opts.base32 ?? false;
  const buf = Buffer.alloc(8);
  // counter as 64-bit big-endian
  let c = BigInt(counter);
  for (let i = 7; i >= 0; i--) {
    buf[i] = Number(c & 0xffn);
    c >>= 8n;
  }
  const key = keyBuffer(secret, base32);
  const hmac = createHmac(algo, key).update(buf).digest();
  const offset = hmac[hmac.length - 1] & 0x0f;
  const code =
    ((hmac[offset] & 0x7f) << 24) |
    ((hmac[offset + 1] & 0xff) << 16) |
    ((hmac[offset + 2] & 0xff) << 8) |
    (hmac[offset + 3] & 0xff);
  const mod = 10 ** digits;
  return String(code % mod).padStart(digits, "0");
}

export function totp(secret, time = Math.floor(Date.now() / 1000), opts = {}) {
  const step = opts.step ?? 30;
  const t0 = opts.t0 ?? 0;
  const counter = Math.floor((time - t0) / step);
  return hotp(secret, counter, opts);
}

export function verify(secret, code, time = Math.floor(Date.now() / 1000), opts = {}) {
  const window = opts.window ?? 1;
  const step = opts.step ?? 30;
  for (let w = -window; w <= window; w++) {
    const t = time + w * step;
    if (totp(secret, t, opts) === String(code).padStart(opts.digits ?? 6, "0")) {
      return true;
    }
  }
  return false;
}