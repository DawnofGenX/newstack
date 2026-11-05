import { request } from "node:http";
import type { CacheEntry } from "./types.js";

export interface Fetched {
  status: number;
  headers: Record<string, string | string[] | undefined>;
  body: string;
  bytes: number;
}

export interface Outcome {
  status: number;
  body: string;
  bytes: number;
  fromCache: boolean;
  revalidated: boolean;
  bodyLost: boolean;
}

export function header(headers: Fetched["headers"], name: string): string | undefined {
  const value = headers[name];
  return Array.isArray(value) ? value[0] : value;
}

export function maxAgeMs(cacheControl: string | undefined): number {
  if (cacheControl === undefined || cacheControl.includes("no-store")) {
    return 0;
  }
  const found = /max-age=(\d+)/.exec(cacheControl);
  return found === null ? 0 : Number(found[1]) * 1000;
}

export function requestOnce(
  origin: string,
  path: string,
  accept: string,
  extra: Record<string, string> = {},
): Promise<Fetched> {
  return new Promise((resolve, reject) => {
    const url = new URL(path, origin);
    const outgoing = request(
      url,
      { method: "GET", headers: { accept, ...extra } },
      (response) => {
        const chunks: Buffer[] = [];
        response.on("data", (chunk: Buffer) => chunks.push(chunk));
        response.on("end", () => {
          const buffer = Buffer.concat(chunks);
          resolve({
            status: response.statusCode ?? 0,
            headers: response.headers,
            body: buffer.toString("utf8"),
            bytes: buffer.byteLength,
          });
        });
      },
    );
    outgoing.on("error", reject);
    outgoing.end();
  });
}

/**
 * A cache is a bet about the future. The bet is placed with Cache-Control, and
 * it is settled with a conditional request: the body is only re-sent when the
 * tag says it changed. Keying by URL alone is the other bet, and Vary is how it
 * loses.
 */
export class HttpCache {
  #origin: string;
  #entries = new Map<string, CacheEntry>();
  #clock: () => number;
  #keyMode: "url" | "vary";
  #dropBodyOn304: boolean;

  constructor(
    origin: string,
    options: { clock?: () => number; keyMode?: "url" | "vary"; dropBodyOn304?: boolean } = {},
  ) {
    this.#origin = origin;
    this.#clock = options.clock ?? (() => Date.now());
    this.#keyMode = options.keyMode ?? "vary";
    this.#dropBodyOn304 = options.dropBodyOn304 ?? false;
  }

  #key(path: string, accept: string): string {
    return this.#keyMode === "url" ? path : `${path}\u0000${accept}`;
  }

  entry(path: string, accept: string): CacheEntry | undefined {
    return this.#entries.get(this.#key(path, accept));
  }

  async get(path: string, accept = "application/json"): Promise<Outcome> {
    const key = this.#key(path, accept);
    const now = this.#clock();
    const entry = this.#entries.get(key);

    if (entry !== undefined && now < entry.expiresAt) {
      entry.hits += 1;
      return { status: 200, body: entry.body, bytes: 0, fromCache: true, revalidated: false, bodyLost: false };
    }

    if (entry !== undefined) {
      entry.stale += 1;
      const conditional = await requestOnce(this.#origin, path, accept, { "if-none-match": entry.etag });
      if (conditional.status === 304) {
        entry.revalidations += 1;
        entry.expiresAt = now + maxAgeMs(header(conditional.headers, "cache-control"));
        entry.etag = header(conditional.headers, "etag") ?? entry.etag;
        if (this.#dropBodyOn304) {
          // The 304 carried no body, so a cache that assigns the response body
          // to its entry erases what it already had. Nothing throws.
          const had = entry.body.length > 0;
          entry.body = conditional.body;
          return { status: 200, body: "", bytes: conditional.bytes, fromCache: false, revalidated: true, bodyLost: had };
        }
        return { status: 200, body: entry.body, bytes: conditional.bytes, fromCache: false, revalidated: true, bodyLost: false };
      }
      this.#store(key, conditional, now);
      return { status: conditional.status, body: conditional.body, bytes: conditional.bytes, fromCache: false, revalidated: false, bodyLost: false };
    }

    const fetched = await requestOnce(this.#origin, path, accept);
    this.#store(key, fetched, now);
    return { status: fetched.status, body: fetched.body, bytes: fetched.bytes, fromCache: false, revalidated: false, bodyLost: false };
  }

  #store(key: string, fetched: Fetched, now: number): void {
    const ttl = maxAgeMs(header(fetched.headers, "cache-control"));
    const etag = header(fetched.headers, "etag");
    if (ttl === 0 || etag === undefined) {
      this.#entries.delete(key);
      return;
    }
    this.#entries.set(key, {
      body: fetched.body,
      etag,
      expiresAt: now + ttl,
      varyKey: header(fetched.headers, "vary") ?? "",
      storedBytes: fetched.bytes,
      revalidations: 0,
      hits: 0,
      misses: 0,
      stale: 0,
    });
  }
}
