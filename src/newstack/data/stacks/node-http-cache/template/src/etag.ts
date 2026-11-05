import { createHash } from "node:crypto";

export interface Tag {
  weak: boolean;
  opaque: string;
}

export function parseTag(text: string): Tag | null {
  const trimmed = text.trim();
  const weak = trimmed.startsWith("W/");
  const quoted = weak ? trimmed.slice(2).trim() : trimmed;
  if (quoted.length < 2 || !quoted.startsWith('"') || !quoted.endsWith('"')) {
    return null;
  }
  return { weak, opaque: quoted.slice(1, -1) };
}

export function renderTag(tag: Tag): string {
  return `${tag.weak ? "W/" : ""}"${tag.opaque}"`;
}

export function strongTag(body: string): string {
  const digest = createHash("sha256").update(body, "utf8").digest("hex").slice(0, 16);
  return `"${digest}"`;
}

export function weakTag(body: string): string {
  return `W/"${createHash("sha256").update(body, "utf8").digest("hex").slice(0, 16)}"`;
}

/**
 * RFC 9110 section 8.8.3.2: the weak comparison ignores the W/ prefix, so a
 * weak tag can satisfy If-None-Match. The strong comparison does not, which is
 * why If-Match with W/"x" never matches anything, not even W/"x" itself.
 */
export function weakCompare(left: Tag, right: Tag): boolean {
  return left.opaque === right.opaque;
}

export function strongCompare(left: Tag, right: Tag): boolean {
  return !left.weak && !right.weak && left.opaque === right.opaque;
}

/** Splits `"a", W/"b", *` into tags; `*` is reported separately because it is not a tag. */
export function parseList(header: string): { any: boolean; tags: Tag[] } {
  let any = false;
  const tags: Tag[] = [];
  for (const piece of header.split(",")) {
    const text = piece.trim();
    if (text === "") {
      continue;
    }
    if (text === "*") {
      any = true;
      continue;
    }
    const tag = parseTag(text);
    if (tag !== null) {
      tags.push(tag);
    }
  }
  return { any, tags };
}

export function anyMatch(header: string, etag: string, mode: "weak" | "strong"): boolean {
  const current = parseTag(etag);
  if (current === null) {
    return false;
  }
  const list = parseList(header);
  if (list.any) {
    return true;
  }
  const compare = mode === "weak" ? weakCompare : strongCompare;
  return list.tags.some((candidate) => compare(candidate, current));
}
