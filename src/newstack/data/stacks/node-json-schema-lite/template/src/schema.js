/**
 * A dependency-free subset of JSON Schema (draft 2020-12 keywords).
 *
 * The goal is a validator that reports every problem with a JSON pointer-ish
 * path instead of stopping at the first one, because the CLI's job is to tell a
 * human what is wrong with their document. Unsupported keywords are ignored
 * rather than throwing: a schema written for a full implementation still
 * validates, it just validates less.
 */

const TYPE_CHECKS = {
  object: (value) => value !== null && typeof value === "object" && !Array.isArray(value),
  array: Array.isArray,
  string: (value) => typeof value === "string",
  number: (value) => typeof value === "number" && Number.isFinite(value),
  integer: (value) => Number.isInteger(value),
  boolean: (value) => typeof value === "boolean",
  null: (value) => value === null,
};

const FORMATS = {
  date: (value) => /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(value)),
  "date-time": (value) => !Number.isNaN(Date.parse(value)) && /T/.test(value),
  email: (value) => /^[^@\s]+@[^@\s.]+\.[^@\s]+$/.test(value),
  uuid: (value) => /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value),
  uri: (value) => /^[a-z][a-z0-9+.-]*:\S+$/i.test(value),
};

export function typeOf(value) {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  if (typeof value === "number") return Number.isInteger(value) ? "integer" : "number";
  return typeof value; // object | string | boolean
}

const child = (path, key) =>
  typeof key === "number" ? `${path}[${key}]` : `${path}.${key}`;

function checkFormat(value, format, path, errors) {
  const rule = FORMATS[format];
  if (rule && typeof value === "string" && !rule(value)) {
    errors.push({ path, message: `does not match format ${format}` });
  }
}

export function validate(value, schema, path = "$", errors = []) {
  if (schema === true || schema === undefined) return errors;
  if (schema === false) {
    errors.push({ path, message: "no value is allowed here" });
    return errors;
  }

  if (schema.type !== undefined) {
    const allowed = Array.isArray(schema.type) ? schema.type : [schema.type];
    const actual = typeOf(value);
    const matches = allowed.some((name) => {
      const check = TYPE_CHECKS[name];
      return check ? check(value) : false;
    });
    // "integer" is also a "number" for the purposes of a wider type list.
    if (!matches) {
      errors.push({ path, message: `expected ${allowed.join(" or ")}, got ${actual}` });
      return errors;
    }
  }

  if (schema.const !== undefined && JSON.stringify(value) !== JSON.stringify(schema.const)) {
    errors.push({ path, message: `must equal ${JSON.stringify(schema.const)}` });
  }

  if (Array.isArray(schema.enum)) {
    const rendered = schema.enum.map((entry) => JSON.stringify(entry) ?? String(entry));
    const hit = schema.enum.some((entry) => JSON.stringify(entry) === JSON.stringify(value));
    if (!hit) errors.push({ path, message: `must be one of ${rendered.join(", ")}` });
  }

  if (typeof value === "string") {
    if (schema.minLength !== undefined && value.length < schema.minLength) {
      errors.push({ path, message: `must be at least ${schema.minLength} characters` });
    }
    if (schema.maxLength !== undefined && value.length > schema.maxLength) {
      errors.push({ path, message: `must be at most ${schema.maxLength} characters` });
    }
    if (schema.pattern !== undefined && !new RegExp(schema.pattern, "u").test(value)) {
      errors.push({ path, message: `does not match pattern ${schema.pattern}` });
    }
    if (schema.format !== undefined) checkFormat(value, schema.format, path, errors);
  }

  if (typeof value === "number") {
    if (schema.minimum !== undefined && value < schema.minimum) {
      errors.push({ path, message: `must be >= ${schema.minimum}` });
    }
    if (schema.maximum !== undefined && value > schema.maximum) {
      errors.push({ path, message: `must be <= ${schema.maximum}` });
    }
    if (schema.exclusiveMinimum !== undefined && value <= schema.exclusiveMinimum) {
      errors.push({ path, message: `must be > ${schema.exclusiveMinimum}` });
    }
    if (schema.exclusiveMaximum !== undefined && value >= schema.exclusiveMaximum) {
      errors.push({ path, message: `must be < ${schema.exclusiveMaximum}` });
    }
    if (schema.multipleOf !== undefined && Math.abs(value / schema.multipleOf % 1) > 1e-9) {
      errors.push({ path, message: `must be a multiple of ${schema.multipleOf}` });
    }
  }

  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems) {
      errors.push({ path, message: `must have at least ${schema.minItems} items` });
    }
    if (schema.maxItems !== undefined && value.length > schema.maxItems) {
      errors.push({ path, message: `must have at most ${schema.maxItems} items` });
    }
    if (schema.uniqueItems === true) {
      const seen = new Set(value.map((entry) => JSON.stringify(entry)));
      if (seen.size !== value.length) errors.push({ path, message: "items must be unique" });
    }
    if (schema.items !== undefined) {
      value.forEach((entry, index) => validate(entry, schema.items, child(path, index), errors));
    }
  }

  if (TYPE_CHECKS.object(value)) {
    for (const key of schema.required ?? []) {
      if (!Object.prototype.hasOwnProperty.call(value, key)) {
        errors.push({ path: child(path, key), message: "is required" });
      }
    }
    const properties = schema.properties ?? {};
    for (const [key, subSchema] of Object.entries(properties)) {
      if (Object.prototype.hasOwnProperty.call(value, key)) {
        validate(value[key], subSchema, child(path, key), errors);
      }
    }
    const extra = Object.keys(value).filter((key) => !(key in properties));
    if (schema.additionalProperties === false && extra.length > 0) {
      for (const key of extra) {
        errors.push({ path: child(path, key), message: "is not an allowed property" });
      }
    } else if (typeof schema.additionalProperties === "object" && schema.additionalProperties !== null) {
      for (const key of extra) {
        validate(value[key], schema.additionalProperties, child(path, key), errors);
      }
    }
    if (schema.minProperties !== undefined && Object.keys(value).length < schema.minProperties) {
      errors.push({ path, message: `must have at least ${schema.minProperties} properties` });
    }
  }

  for (const branch of schema.allOf ?? []) validate(value, branch, path, errors);

  if (Array.isArray(schema.anyOf)) {
    const attempts = schema.anyOf.map((branch) => validate(value, branch, path, []));
    if (attempts.every((attempt) => attempt.length > 0)) {
      errors.push({ path, message: "must match at least one of the anyOf branches" });
    }
  }

  if (Array.isArray(schema.oneOf)) {
    const passing = schema.oneOf
      .map((branch) => validate(value, branch, path, []))
      .filter((attempt) => attempt.length === 0);
    if (passing.length !== 1) {
      errors.push({ path, message: `must match exactly one oneOf branch, matched ${passing.length}` });
    }
  }

  if (schema.not !== undefined && validate(value, schema.not, path, []).length === 0) {
    errors.push({ path, message: "must not match the not schema" });
  }

  return errors;
}

export function isValid(value, schema) {
  return validate(value, schema).length === 0;
}
