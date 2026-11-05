// exposition.js — a strict reader for the Prometheus text exposition format.
//
// A scraper rejects the WHOLE payload when one line is malformed, and the failure
// message names a line number you have to bisect by hand. This parser is the same
// contract, checked in-process: HELP/TYPE once per family, counters ending in
// `_total`, cumulative histogram buckets that end at +Inf and equal `_count`, and
// label values with the three escapes the format allows.

const TYPES = new Set(["counter", "gauge", "histogram", "summary"]);
const SAMPLE = /^([a-zA-Z_:][a-zA-Z0-9_:]*)(\{[^}]*\})? (\S+)$/;
const LABEL = /([a-zA-Z_][a-zA-Z0-9_]*)="((?:[^"\\]|\\.)*)"/g;
const VALUE = /^(?:-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?|NaN|[+-]Inf)$/;

export function unescapeLabelValue(value) {
  return value.replace(/\\(.)/g, (_, char) => (char === "n" ? "\n" : char));
}

export function parseLabels(raw) {
  const labels = {};
  if (!raw) return labels;
  const inner = raw.slice(1, -1);
  let consumed = 0;
  for (const match of inner.matchAll(LABEL)) {
    labels[match[1]] = unescapeLabelValue(match[2]);
    consumed += match[0].length + 1; // + the comma that follows (or trails)
  }
  if (inner.length && consumed < inner.length && inner.length - consumed > 1) {
    throw new Error(`unparsable label list: ${inner}`);
  }
  return labels;
}

export function parseExposition(text) {
  if (typeof text !== "string" || text.length === 0) throw new Error("empty exposition");
  if (!text.endsWith("\n")) throw new Error("exposition must end with a newline");

  const families = new Map();
  const series = new Set();
  const lines = text.slice(0, -1).split("\n");

  lines.forEach((line, index) => {
    const where = `line ${index + 1}`;
    if (line.trim() === "") throw new Error(`${where}: blank line`);
    if (line.startsWith("#")) {
      const parts = line.split(" ");
      const kind = parts[1];
      const name = parts[2];
      if (kind === "HELP") {
        const family = families.get(name) || { name, type: null, help: null, samples: [] };
        if (family.help !== null) throw new Error(`${where}: duplicate HELP for ${name}`);
        family.help = parts.slice(3).join(" ");
        families.set(name, family);
        return;
      }
      if (kind === "TYPE") {
        const family = families.get(name) || { name, type: null, help: null, samples: [] };
        if (family.type !== null) throw new Error(`${where}: duplicate TYPE for ${name}`);
        if (!TYPES.has(parts[3])) throw new Error(`${where}: unknown type ${parts[3]}`);
        family.type = parts[3];
        families.set(name, family);
        return;
      }
      throw new Error(`${where}: unknown comment ${line}`);
    }

    const match = SAMPLE.exec(line);
    if (!match) throw new Error(`${where}: unparsable sample ${JSON.stringify(line)}`);
    const [, metric, labelText, rawValue] = match;
    if (!VALUE.test(rawValue)) throw new Error(`${where}: bad value ${rawValue}`);
    const labels = parseLabels(labelText);

    const key = `${metric}${JSON.stringify(Object.entries(labels).sort())}`;
    if (series.has(key)) throw new Error(`${where}: duplicate series ${key}`);
    series.add(key);

    // A sample belongs to `foo_<suffix>` when the suffix is a histogram part.
    const base = metric.replace(/_(bucket|sum|count)$/, "");
    const family = families.get(base) || families.get(metric);
    if (!family) throw new Error(`${where}: no HELP/TYPE for ${metric}`);
    family.samples.push({ metric, labels, value: Number(rawValue) });
  });

  for (const family of families.values()) {
    if (family.help === null) throw new Error(`${family.name}: TYPE without HELP`);
    if (family.type === null) throw new Error(`${family.name}: HELP without TYPE`);
    if (family.type === "counter" && !family.name.endsWith("_total")) {
      throw new Error(`${family.name}: a counter must be named ..._total`);
    }
  }
  for (const family of families.values()) {
    if (family.type === "histogram") validateHistogram(family);
  }
  return families;
}

function validateHistogram(family) {
  const groups = new Map();
  for (const sample of family.samples) {
    if (sample.metric === family.name) {
      throw new Error(`${family.name}: a histogram has no bare sample`);
    }
    const parts = /^(.*)_(bucket|sum|count)$/.exec(sample.metric);
    if (!parts) throw new Error(`${family.name}: unexpected sample ${sample.metric}`);
    const { le, ...rest } = sample.labels;
    const groupKey = JSON.stringify(Object.entries(rest).sort());
    const group = groups.get(groupKey) || { buckets: [], sum: null, count: null };
    if (parts[2] === "bucket") {
      if (le === undefined) throw new Error(`${sample.metric}: missing le label`);
      group.buckets.push({ le, value: sample.value });
    } else if (parts[2] === "sum") {
      group.sum = sample.value;
    } else {
      group.count = sample.value;
    }
    groups.set(groupKey, group);
  }

  for (const [key, group] of groups) {
    if (group.sum === null) throw new Error(`${family.name}${key}: missing _sum`);
    if (group.count === null) throw new Error(`${family.name}${key}: missing _count`);
    const infinity = group.buckets.filter((bucket) => bucket.le === "+Inf");
    if (infinity.length !== 1) {
      throw new Error(`${family.name}${key}: exactly one +Inf bucket is required`);
    }
    if (infinity[0].value !== group.count) {
      throw new Error(
        `${family.name}${key}: +Inf bucket ${infinity[0].value} must equal _count ${group.count}`,
      );
    }
    const finite = group.buckets
      .filter((bucket) => bucket.le !== "+Inf")
      .map((bucket) => ({ bound: Number(bucket.le), value: bucket.value }))
      .sort((a, b) => a.bound - b.bound);
    let previous = 0;
    for (const bucket of finite) {
      if (!Number.isFinite(bucket.bound)) throw new Error(`${family.name}: bad le ${bucket.le}`);
      if (bucket.value < previous) {
        throw new Error(`${family.name}${key}: buckets must be cumulative and non-decreasing`);
      }
      previous = bucket.value;
    }
    if (previous > group.count) {
      throw new Error(`${family.name}${key}: a finite bucket exceeds _count`);
    }
  }
}

export function sampleValue(families, metric, labels = {}) {
  const base = metric.replace(/_(bucket|sum|count)$/, "");
  const family = families.get(base) || families.get(metric);
  if (!family) throw new Error(`no family ${metric}`);
  const wanted = JSON.stringify(Object.entries(labels).sort());
  const hits = family.samples.filter(
    (sample) =>
      sample.metric === metric &&
      JSON.stringify(Object.entries(sample.labels).sort()) === wanted,
  );
  if (hits.length !== 1) throw new Error(`${metric}${wanted}: ${hits.length} samples`);
  return hits[0].value;
}
