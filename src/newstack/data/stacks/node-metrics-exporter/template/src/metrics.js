// metrics.js — a tiny, strict Prometheus registry.
//
// The exposition format has rules that are easy to break silently: one HELP/TYPE
// per family, cumulative buckets, a mandatory +Inf bucket that must equal _count,
// and label values that need escaping. Prometheus rejects the whole scrape when
// one line is wrong, so the format is treated as a contract here, not a printf.

const RESERVED_SUFFIXES = ["_total", "_bucket", "_sum", "_count", "_info"];

export function escapeLabelValue(value) {
  return String(value)
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"')
    .replace(/\n/g, "\\n");
}

export function formatLabels(labels) {
  const keys = Object.keys(labels || {}).sort();
  if (keys.length === 0) return "";
  const pairs = keys.map((key) => `${key}="${escapeLabelValue(labels[key])}"`);
  return `{${pairs.join(",")}}`;
}

function seriesKey(name, labels) {
  return `${name}${formatLabels(labels)}`;
}

function checkValue(name, value) {
  if (!Number.isFinite(value)) {
    throw new TypeError(`${name}: sample value must be finite, got ${value}`);
  }
}

export class Registry {
  constructor({ now = () => process.hrtime.bigint() } = {}) {
    this.now = now;
    this.families = new Map();
  }

  #family(name, type, help) {
    const existing = this.families.get(name);
    if (existing) {
      if (existing.type !== type) {
        throw new TypeError(`${name}: already registered as ${existing.type}, not ${type}`);
      }
      return existing;
    }
    if (type === "counter") {
      // promlint's first rule: a counter is spelled `..._total`. Getting this wrong
      // does not fail the scrape, it fails years of dashboards.
      if (!name.endsWith("_total")) {
        throw new TypeError(`${name}: a counter name must end with _total`);
      }
    } else {
      for (const suffix of RESERVED_SUFFIXES) {
        if (suffix !== "_total" && name.endsWith(suffix)) {
          // `_bucket`, `_sum` and `_count` are produced by the histogram renderer.
          throw new TypeError(`${name}: a ${type} must not carry the reserved suffix ${suffix}`);
        }
      }
    }
    const family = { name, type, help, samples: new Map() };
    this.families.set(name, family);
    return family;
  }

  counter(name, help) {
    return this.#family(name, "counter", help);
  }

  gauge(name, help) {
    return this.#family(name, "gauge", help);
  }

  histogram(name, help, buckets) {
    const family = this.#family(name, "histogram", help);
    if (!family.buckets) {
      const sorted = [...buckets].sort((a, b) => a - b);
      if (sorted.length === 0 || sorted[sorted.length - 1] === Infinity) {
        throw new TypeError(`${name}: pass finite buckets; +Inf is added automatically`);
      }
      family.buckets = sorted;
    }
    return family;
  }

  inc(name, labels = {}, amount = 1) {
    const family = this.families.get(name);
    if (!family || family.type !== "counter") throw new TypeError(`${name}: not a counter`);
    if (amount < 0) throw new RangeError(`${name}: counters only go up, got ${amount}`);
    const key = seriesKey(name, labels);
    const current = family.samples.get(key) || { labels, value: 0 };
    current.value += amount;
    checkValue(name, current.value);
    family.samples.set(key, current);
  }

  add(name, labels = {}, delta = 1) {
    const family = this.families.get(name);
    if (!family || family.type !== "gauge") throw new TypeError(`${name}: not a gauge`);
    const key = seriesKey(name, labels);
    const current = family.samples.get(key) || { labels, value: 0 };
    current.value += delta;
    checkValue(name, current.value);
    family.samples.set(key, current);
  }

  set(name, value, labels = {}) {
    const family = this.families.get(name);
    if (!family || family.type !== "gauge") throw new TypeError(`${name}: not a gauge`);
    checkValue(name, value);
    family.samples.set(seriesKey(name, labels), { labels, value });
  }

  observe(name, value, labels = {}) {
    const family = this.families.get(name);
    if (!family || family.type !== "histogram") throw new TypeError(`${name}: not a histogram`);
    checkValue(name, value);
    if (value < 0) throw new RangeError(`${name}: a duration cannot be negative`);
    const key = seriesKey(name, labels);
    const current = family.samples.get(key) || {
      labels,
      counts: new Array(family.buckets.length).fill(0),
      sum: 0,
      count: 0,
    };
    // Cumulative buckets: an observation lands in every bucket it is <= to.
    for (let index = 0; index < family.buckets.length; index += 1) {
      if (value <= family.buckets[index]) current.counts[index] += 1;
    }
    current.sum += value;
    current.count += 1;
    family.samples.set(key, current);
  }

  render() {
    const lines = [];
    for (const name of [...this.families.keys()].sort()) {
      const family = this.families.get(name);
      lines.push(`# HELP ${name} ${family.help}`);
      lines.push(`# TYPE ${name} ${family.type}`);
      const samples = [...family.samples.values()].sort((a, b) =>
        formatLabels(a.labels).localeCompare(formatLabels(b.labels)),
      );
      if (family.type === "histogram") {
        for (const sample of samples) {
          family.buckets.forEach((bound, index) => {
            const labels = { ...sample.labels, le: String(bound) };
            lines.push(`${name}_bucket${formatLabels(labels)} ${sample.counts[index]}`);
          });
          lines.push(`${name}_bucket${formatLabels({ ...sample.labels, le: "+Inf" })} ${sample.count}`);
          lines.push(`${name}_sum${formatLabels(sample.labels)} ${sample.sum}`);
          lines.push(`${name}_count${formatLabels(sample.labels)} ${sample.count}`);
        }
        continue;
      }
      for (const sample of samples) {
        lines.push(`${seriesKey(name, sample.labels)} ${sample.value}`);
      }
    }
    return `${lines.join("\n")}\n`;
  }
}
