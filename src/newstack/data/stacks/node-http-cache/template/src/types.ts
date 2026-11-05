export interface Document {
  path: string;
  body: string;
  version: number;
  changedAt: number;
  maxAgeMs: number;
  varyAccept: boolean;
}

export interface Response {
  status: number;
  headers: Record<string, string>;
  body: string;
  bytes: number;
  revalidated: boolean;
}

export interface CacheEntry {
  body: string;
  etag: string;
  expiresAt: number;
  varyKey: string;
  storedBytes: number;
  revalidations: number;
  hits: number;
  misses: number;
  stale: number;
}

export const EMPTY_304_SAVING = 0;
