const NUM = /^\d+$/;

export function parse(version) {
  const v = String(version).trim().replace(/^v/, "");
  const [core, pre] = v.split("-", 2);
  const parts = core.split(".");
  if (parts.length !== 3) throw new Error(`invalid version: ${version}`);
  const [major, minor, patch] = parts.map((p) => {
    if (!NUM.test(p)) throw new Error(`invalid version: ${version}`);
    return Number(p);
  });
  const prerelease = pre ? pre.split(".") : [];
  return { major, minor, patch, prerelease, raw: v };
}

export function comparePre(a, b) {
  if (a.length === 0 && b.length === 0) return 0;
  if (a.length === 0) return 1; // no prerelease > prerelease
  if (b.length === 0) return -1;
  const n = Math.max(a.length, b.length);
  for (let i = 0; i < n; i++) {
    if (i >= a.length) return -1;
    if (i >= b.length) return 1;
    const x = a[i], y = b[i];
    const xn = NUM.test(x), yn = NUM.test(y);
    if (xn && yn) {
      const d = Number(x) - Number(y);
      if (d !== 0) return d < 0 ? -1 : 1;
    } else if (xn !== yn) {
      return xn ? -1 : 1;
    } else {
      if (x < y) return -1;
      if (x > y) return 1;
    }
  }
  return 0;
}

export function compare(a, b) {
  const pa = typeof a === "string" ? parse(a) : a;
  const pb = typeof b === "string" ? parse(b) : b;
  if (pa.major !== pb.major) return pa.major < pb.major ? -1 : 1;
  if (pa.minor !== pb.minor) return pa.minor < pb.minor ? -1 : 1;
  if (pa.patch !== pb.patch) return pa.patch < pb.patch ? -1 : 1;
  return comparePre(pa.prerelease, pb.prerelease);
}

function splitRange(range) {
  const r = String(range).trim();
  // hyphen range
  const m = r.match(/^(.+?)\s+-\s+(.+)$/);
  if (m) return { type: "hyphen", low: m[1].trim(), high: m[2].trim() };
  // operators
  const opMatch = r.match(/^(>=|<=|>|<|\^|~|=)?\s*(.+)$/);
  const op = opMatch[1] || "";
  const ver = opMatch[2].trim();
  // space-separated AND (>=1.0.0 <2.0.0)
  if (r.includes(" ") && !r.includes(" - ")) {
    return { type: "and", parts: r.split(/\s+/).map(splitRange) };
  }
  return { type: "op", op, ver };
}

export function satisfies(version, range) {
  const v = parse(version);
  const r = splitRange(range);
  if (r.type === "hyphen") {
    return compare(v, parse(r.low)) >= 0 && compare(v, parse(r.high)) <= 0;
  }
  if (r.type === "and") {
    return r.parts.every((p) => satisfies(version, reconstruct(p)));
  }
  const { op, ver } = r;
  const target = parse(ver);
  if (op === "" || op === "=") {
    return compare(v, target) === 0;
  }
  if (op === ">=") return compare(v, target) >= 0;
  if (op === "<=") return compare(v, target) <= 0;
  if (op === ">") return compare(v, target) > 0;
  if (op === "<") return compare(v, target) < 0;
  if (op === "^") {
    // caret
    if (target.major > 0) {
      return compare(v, target) >= 0 && v.major === target.major;
    }
    if (target.minor > 0) {
      return compare(v, target) >= 0 && v.major === 0 && v.minor === target.minor;
    }
    return compare(v, target) >= 0 && v.major === 0 && v.minor === 0 && v.patch === target.patch;
  }
  if (op === "~") {
    // tilde
    if (ver.split(".").length <= 2) {
      // ~1.2 := >=1.2.0 <1.3.0
      return compare(v, target) >= 0 && v.major === target.major && v.minor === target.minor;
    }
    return compare(v, target) >= 0 && v.major === target.major && v.minor === target.minor;
  }
  throw new Error(`unsupported range: ${range}`);
}

function reconstruct(p) {
  if (p.type === "op") return `${p.op}${p.ver}`.trim() || p.ver;
  if (p.type === "hyphen") return `${p.low} - ${p.high}`;
  return "";
}
