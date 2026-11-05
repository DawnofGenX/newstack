import type { Document } from "./types.js";

export class DocumentError extends Error {}

export function document(
  path: string,
  fields: Record<string, string | number>,
  options: { maxAgeMs?: number; varyAccept?: boolean; changedAt?: number } = {},
): Document {
  if (!path.startsWith("/")) {
    throw new DocumentError(`document path ${path} must start with /`);
  }
  return {
    path,
    body: JSON.stringify(fields, null, 2),
    version: 1,
    changedAt: options.changedAt ?? 1_700_000_000_000,
    maxAgeMs: options.maxAgeMs ?? 60_000,
    varyAccept: options.varyAccept ?? false,
  };
}

/** The representation a client asked for. The URL alone is not enough when Vary is set. */
export function representation(doc: Document, accept: string): string {
  if (!doc.varyAccept) {
    return doc.body;
  }
  return accept.includes("text/plain") ? `${doc.path} v${doc.version}\n` : doc.body;
}

export function cacheControl(doc: Document): string {
  return doc.maxAgeMs === 0 ? "no-store" : `max-age=${Math.floor(doc.maxAgeMs / 1000)}`;
}

export function isFresh(doc: Document, at: number): boolean {
  return at < doc.changedAt + doc.maxAgeMs;
}

export class Library {
  #docs = new Map<string, Document>();
  #clock: () => number;

  constructor(docs: Document[], clock: () => number = () => Date.now()) {
    for (const doc of docs) {
      this.#docs.set(doc.path, doc);
    }
    this.#clock = clock;
  }

  get(path: string): Document | undefined {
    return this.#docs.get(path);
  }

  paths(): string[] {
    return [...this.#docs.keys()].sort();
  }

  /** A write needs the version it saw, expressed as If-Match; that is what makes it conditional. */
  write(path: string, body: string, version: number): Document {
    const doc = this.#docs.get(path);
    if (doc === undefined) {
      throw new DocumentError(`no document at ${path}`);
    }
    if (doc.version !== version) {
      throw new DocumentError(
        `document ${path} is at version ${doc.version}, not ${version}: the write was built on a state that is gone`,
      );
    }
    const next: Document = {
      ...doc,
      body,
      version: doc.version + 1,
      changedAt: this.#clock(),
    };
    this.#docs.set(path, next);
    return next;
  }
}
