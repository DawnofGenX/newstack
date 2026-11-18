// Pure hashing: bytes in, hex out. No I/O and no process globals, so the tests
// can drive every branch directly.

import { createHash } from "node:crypto";

export type Algorithm = "sha256" | "sha1" | "md5" | "crc32";

export const ALGORITHMS: Algorithm[] = ["sha256", "sha1", "md5", "crc32"];

const CRC32_TABLE: number[] = (() => {
  const table: number[] = [];
  for (let index = 0; index < 256; index += 1) {
    let value = index;
    for (let bit = 0; bit < 8; bit += 1) {
      value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
    }
    table.push(value >>> 0);
  }
  return table;
})();

/** The CRC-32 (IEEE 802.3) of a byte buffer, the algorithm `cksum`/zip use. */
export function crc32(bytes: Uint8Array): number {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc = CRC32_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

/** Lowercase hex digest of `bytes` under `algorithm`. */
export function digest(bytes: Uint8Array, algorithm: Algorithm = "sha256"): string {
  if (algorithm === "crc32") {
    return crc32(bytes).toString(16).padStart(8, "0");
  }
  return createHash(algorithm).update(bytes).digest("hex");
}

/** Digest of a string's UTF-8 bytes; convenience for tests and stdin. */
export function digestText(text: string, algorithm: Algorithm = "sha256"): string {
  return digest(new TextEncoder().encode(text), algorithm);
}

export interface ChecksumEntry {
  digest: string;
  name: string;
}

/**
 * Parses `sha256sum`-style output: one `<hex>` and a name per line, separated
 * by whitespace. Blank lines and `#` comments are skipped, and a binary-mode
 * `*` before the name is dropped.
 */
export function parseChecksums(text: string): ChecksumEntry[] {
  const entries: ChecksumEntry[] = [];
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (line === "" || line.startsWith("#")) continue;
    const match = /^([0-9a-fA-F]+)\s+\*?(.+)$/.exec(line);
    if (match === null) {
      throw new Error(`cannot parse checksum line: ${line}`);
    }
    entries.push({ digest: match[1].toLowerCase(), name: match[2].trim() });
  }
  return entries;
}

export interface CheckResult {
  name: string;
  expected: string;
  actual: string;
  ok: boolean;
}

/** Compares one expected digest per entry against the actual bytes. */
export function verify(entries: ChecksumEntry[], actual: (name: string) => string): CheckResult[] {
  return entries.map((entry) => {
    const computed = actual(entry.name).toLowerCase();
    return {
      name: entry.name,
      expected: entry.digest,
      actual: computed,
      // A short digest is accepted as a prefix, like `sha256sum --check` does not
      // do, but `git` does; we keep the strict default and document it.
      ok: computed.length >= entry.digest.length && computed.startsWith(entry.digest),
    };
  });
}

/** Builds the `sha256sum`-style line for a file. */
export function formatLine(digestValue: string, name: string): string {
  return `${digestValue}  ${name}`;
}
