// UUIDv7, as specified in RFC 9562: a 48-bit big-endian millisecond timestamp
// followed by 74 random bits, so identifiers sort by creation time as plain
// strings while staying unguessable.

export type UuidVersion = 1 | 4 | 7;

export type ParsedUuid = {
  /** Lowercase canonical form with dashes. */
  text: string;
  version: UuidVersion;
  /** RFC 4122 variant (10xx) present. */
  variant: boolean;
  /** Creation time in milliseconds for a v7, null for anything else. */
  timestampMs: number | null;
  /** The 16 bytes, in order. */
  bytes: Uint8Array;
};

const HEX = "0123456789abcdef";
const CANONICAL = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

export function toHex(bytes: Uint8Array): string {
  let out = "";
  for (const byte of bytes) out += HEX[byte >> 4] + HEX[byte & 0x0f];
  return out;
}

export function fromHex(text: string): Uint8Array {
  if (text.length % 2 !== 0) throw new Error(`odd number of hex digits: ${text.length}`);
  const bytes = new Uint8Array(text.length / 2);
  for (let i = 0; i < bytes.length; i++) {
    const pair = text.slice(i * 2, i * 2 + 2);
    if (!/^[0-9a-f]{2}$/.test(pair)) throw new Error(`invalid hex pair: ${pair}`);
    bytes[i] = Number.parseInt(pair, 16);
  }
  return bytes;
}

export function format(bytes: Uint8Array): string {
  if (bytes.length !== 16) throw new Error(`a uuid is 16 bytes, got ${bytes.length}`);
  const hex = toHex(bytes);
  return [hex.slice(0, 8), hex.slice(8, 12), hex.slice(12, 16), hex.slice(16, 20), hex.slice(20)].join("-");
}

/**
 * Builds a v7 uuid from an explicit millisecond timestamp and ten random bytes,
 * so callers (and tests) never depend on the clock or on crypto.
 *
 *   bytes 0-5   timestamp, 48 bits big-endian
 *   byte  6     version nibble 0111, plus 4 random bits
 *   byte  7     8 random bits
 *   byte  8     variant 10, plus 6 random bits
 *   bytes 9-15  56 random bits
 */
export function uuidV7(timestampMs: number, random: Uint8Array): Uint8Array {
  if (!Number.isInteger(timestampMs) || timestampMs < 0 || timestampMs > 0xffffffffffff) {
    throw new Error(`timestamp out of range for 48 bits: ${timestampMs}`);
  }
  if (random.length < 10) throw new Error(`need 10 random bytes, got ${random.length}`);

  const bytes = new Uint8Array(16);
  const stamp = BigInt(timestampMs);
  for (let i = 5; i >= 0; i--) {
    bytes[i] = Number((stamp >> BigInt((5 - i) * 8)) & 0xffn);
  }
  bytes[6] = 0x70 | (random[0] & 0x0f);
  bytes[7] = random[1];
  bytes[8] = 0x80 | (random[2] & 0x3f);
  for (let i = 0; i < 7; i++) bytes[9 + i] = random[3 + i];
  return bytes;
}

export function isCanonical(text: string): boolean {
  return CANONICAL.test(text);
}

export function parse(text: string): ParsedUuid {
  const lower = text.trim().toLowerCase();
  if (!CANONICAL.test(lower)) throw new Error(`not a canonical uuid: ${text}`);
  const bytes = fromHex(lower.replaceAll("-", ""));

  const versionNibble = bytes[6] >> 4;
  if (versionNibble !== 1 && versionNibble !== 4 && versionNibble !== 7) {
    throw new Error(`unsupported uuid version ${versionNibble} (expected 1, 4 or 7)`);
  }
  const variant = (bytes[8] & 0xc0) === 0x80;

  let timestampMs: number | null = null;
  if (versionNibble === 7) {
    let stamp = 0n;
    for (let i = 0; i < 6; i++) stamp = (stamp << 8n) | BigInt(bytes[i]);
    if (stamp > BigInt(Number.MAX_SAFE_INTEGER)) throw new Error("timestamp exceeds Number.MAX_SAFE_INTEGER");
    timestampMs = Number(stamp);
  }

  return { text: lower, version: versionNibble as UuidVersion, variant, timestampMs, bytes };
}

export function isUuid(text: string): boolean {
  if (!isCanonical(text.trim().toLowerCase())) return false;
  try {
    parse(text);
    return true;
  } catch {
    return false;
  }
}

/** Lexicographic order of canonical text equals generation order for v7. */
export function compare(left: string, right: string): number {
  return left.trim().toLowerCase() < right.trim().toLowerCase()
    ? -1
    : left.trim().toLowerCase() > right.trim().toLowerCase()
      ? 1
      : 0;
}

/** RFC 9562 epoch: a v7 timestamp counts milliseconds from 1970-01-01. */
export function timestampToIso(timestampMs: number): string {
  return new Date(timestampMs).toISOString();
}
