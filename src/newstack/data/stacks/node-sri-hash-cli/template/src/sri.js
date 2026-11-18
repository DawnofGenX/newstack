import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";

export const ALGORITHMS = ["sha256", "sha384", "sha512"];

export function sriFor(buffer, algorithm = "sha384") {
  if (!ALGORITHMS.includes(algorithm)) throw new Error(`unsupported algorithm: ${algorithm}`);
  return `${algorithm}-${createHash(algorithm).update(buffer).digest("base64")}`;
}

export function parseSri(value) {
  return String(value)
    .trim()
    .split(/\s+/)
    .filter(Boolean)
    .map((token) => {
      const dash = token.indexOf("-");
      if (dash === -1) throw new Error(`malformed integrity token: ${token}`);
      const algorithm = token.slice(0, dash);
      if (!ALGORITHMS.includes(algorithm)) throw new Error(`unsupported algorithm: ${algorithm}`);
      return { algorithm, digest: token.slice(dash + 1) };
    });
}

export function verify(buffer, integrity) {
  const tokens = parseSri(integrity);
  if (tokens.length === 0) throw new Error("no integrity tokens given");
  return tokens.some(({ algorithm, digest }) => createHash(algorithm).update(buffer).digest("base64") === digest);
}

export function verifyManifest(dir, manifest) {
  const results = [];
  for (const [file, integrity] of Object.entries(manifest)) {
    const buffer = readFileSync(join(dir, file));
    results.push({ file, ok: verify(buffer, integrity) });
  }
  return results;
}

export function readManifest(path) {
  const manifest = JSON.parse(readFileSync(path, "utf8"));
  return { dir: dirname(path), manifest };
}
