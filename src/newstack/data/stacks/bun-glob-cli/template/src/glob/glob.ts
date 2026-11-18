/**
 * A glob matcher for the subset shells and build tools agree on:
 * `*` (within a segment), `**` (across segments), `?`, `[abc]`, `[!abc]` and
 * `{a,b}` alternatives. No dependencies, no filesystem access: this module only
 * turns a pattern into a RegExp and tests strings against it.
 */

const SPECIAL = /[.+^$\(\)|\\]/g;

function escapeLiteral(text: string): string {
  return text.replace(SPECIAL, "\\$&");
}

/** Splits `a,b` on the commas that are not inside a nested `{...}`. */
function splitTopLevel(inner: string): string[] {
  const parts: string[] = [];
  let depth = 0;
  let start = 0;
  for (let i = 0; i < inner.length; i += 1) {
    const char = inner[i];
    if (char === "{") depth += 1;
    else if (char === "}") depth -= 1;
    else if (char === "," && depth === 0) {
      parts.push(inner.slice(start, i));
      start = i + 1;
    }
  }
  parts.push(inner.slice(start));
  return parts;
}

/** `src/{a,b}/*.ts` becomes `["src/a/*.ts", "src/b/*.ts"]`. */
export function expandBraces(pattern: string): string[] {
  const open = pattern.indexOf("{");
  if (open === -1) return [pattern];

  let depth = 0;
  let close = -1;
  for (let i = open; i < pattern.length; i += 1) {
    if (pattern[i] === "{") depth += 1;
    else if (pattern[i] === "}") {
      depth -= 1;
      if (depth === 0) {
        close = i;
        break;
      }
    }
  }

  // An unbalanced brace is a literal brace, which is what every shell does.
  if (close === -1) return [pattern];

  const before = pattern.slice(0, open);
  const inner = pattern.slice(open + 1, close);
  const after = pattern.slice(close + 1);
  const results: string[] = [];
  for (const option of splitTopLevel(inner)) {
    // Recurse on the joined text, not just the tail: the option itself may hold
    // another brace group, as in `x.{js,{m,c}js}`.
    results.push(...expandBraces(before + option + after));
  }
  return results;
}

function compileOne(pattern: string): string {
  let out = "";
  for (let i = 0; i < pattern.length; i += 1) {
    const char = pattern[i] as string;

    if (char === "*") {
      if (pattern[i + 1] === "*") {
        if (pattern[i + 2] === "/") {
          // `**/` matches zero or more whole segments, so `**/a.ts` also
          // matches a top-level `a.ts`.
          out += "(?:[^/]+/)*";
          i += 2;
        } else {
          out += ".*";
          i += 1;
        }
        continue;
      }
      out += "[^/]*";
      continue;
    }

    if (char === "?") {
      out += "[^/]";
      continue;
    }

    if (char === "[") {
      const end = pattern.indexOf("]", i + 1);
      if (end === -1) {
        out += "\\[";
        continue;
      }
      const body = pattern.slice(i + 1, end);
      const negated = body.startsWith("!") || body.startsWith("^");
      const characters = (negated ? body.slice(1) : body).replace(/\\/g, "\\\\");
      out += negated ? `[^/${characters}]` : `[${characters}]`;
      i = end;
      continue;
    }

    out += escapeLiteral(char);
  }
  return out;
}

/** Compiles a pattern (with braces expanded) into one anchored RegExp. */
export function globToRegExp(pattern: string): RegExp {
  const alternatives = expandBraces(pattern).map(compileOne);
  return new RegExp(`^(?:${alternatives.join("|")})$`);
}

/** True when `path` matches `pattern`. Paths use forward slashes either way. */
export function matches(pattern: string, path: string): boolean {
  return globToRegExp(pattern).test(path.replace(/\\/g, "/"));
}

/** True when any of the patterns matches; an empty list never matches. */
export function matchesAny(patterns: string[], path: string): boolean {
  return patterns.some((pattern) => matches(pattern, path));
}

/** Drops the `./` prefix, collapses `//` and removes trailing slashes. */
export function normalise(path: string): string {
  return path
    .replace(/\\/g, "/")
    .replace(/^\.\//, "")
    .replace(/\/{2,}/g, "/")
    .replace(/(.)\/$/, "$1");
}
