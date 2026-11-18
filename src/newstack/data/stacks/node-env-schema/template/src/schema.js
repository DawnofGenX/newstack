export const TYPES = ["string", "number", "boolean", "url", "enum"];

export function parseDotEnv(text) {
  const out = {};
  for (const rawLine of String(text).split(/\r?\n/)) {
    let line = rawLine.trim();
    if (!line || line.startsWith("#")) continue;
    if (line.startsWith("export ")) line = line.slice(7).trim();
    const eq = line.indexOf("=");
    if (eq === -1) throw new Error(`malformed line: ${rawLine}`);
    const key = line.slice(0, eq).trim();
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(key)) throw new Error(`invalid key: ${key}`);
    let value = line.slice(eq + 1).trim();
    if (value.startsWith('"') || value.startsWith("'")) {
      const quote = value[0];
      const end = value.indexOf(quote, 1);
      if (end === -1) throw new Error(`unterminated quoted value: ${key}`);
      value = value.slice(1, end);
    } else {
      const hash = value.indexOf(" #");
      if (hash !== -1) value = value.slice(0, hash);
      value = value.trim();
    }
    if (Object.prototype.hasOwnProperty.call(out, key)) throw new Error(`duplicate key: ${key}`);
    out[key] = value;
  }
  return out;
}

function coerceNumber(key, value, spec) {
  const n = Number(value);
  if (value === "" || Number.isNaN(n)) throw new Error(`${key} must be a number, got "${value}"`);
  if (spec.integer && !Number.isInteger(n)) throw new Error(`${key} must be an integer, got ${n}`);
  if (spec.min !== undefined && n < spec.min) throw new Error(`${key} must be >= ${spec.min}, got ${n}`);
  if (spec.max !== undefined && n > spec.max) throw new Error(`${key} must be <= ${spec.max}, got ${n}`);
  return n;
}

function coerceBoolean(key, value) {
  const v = String(value).toLowerCase();
  if (["1", "true", "yes", "on"].includes(v)) return true;
  if (["0", "false", "no", "off"].includes(v)) return false;
  throw new Error(`${key} must be a boolean, got "${value}"`);
}

export function coerce(key, value, spec) {
  switch (spec.type ?? "string") {
    case "string":
      return String(value);
    case "number":
      return coerceNumber(key, value, spec);
    case "boolean":
      return coerceBoolean(key, value);
    case "url": {
      try {
        const url = new URL(String(value));
        if (!url.protocol.startsWith("http")) throw new Error("protocol");
        return url.toString();
      } catch {
        throw new Error(`${key} must be an http(s) url, got "${value}"`);
      }
    }
    case "enum": {
      const allowed = spec.values ?? [];
      if (!allowed.includes(String(value))) throw new Error(`${key} must be one of ${allowed.join(", ")}, got "${value}"`);
      return String(value);
    }
    default:
      throw new Error(`unknown type for ${key}: ${spec.type}`);
  }
}

export function validateEnv(env, schema) {
  const values = {};
  const errors = [];
  for (const [key, spec] of Object.entries(schema)) {
    const present = Object.prototype.hasOwnProperty.call(env, key);
    if (!present) {
      if (spec.required) errors.push(`${key} is required`);
      else if (spec.default !== undefined) values[key] = spec.default;
      continue;
    }
    try {
      values[key] = coerce(key, env[key], spec);
    } catch (err) {
      errors.push(err.message);
    }
  }
  for (const key of Object.keys(env)) {
    if (!Object.prototype.hasOwnProperty.call(schema, key)) errors.push(`${key} is not in the schema`);
  }
  return { values, errors };
}
