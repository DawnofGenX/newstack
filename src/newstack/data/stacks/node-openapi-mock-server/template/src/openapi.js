import { readFileSync } from "node:fs";

export function loadSpec(path) {
  const raw = readFileSync(path, "utf8");
  const spec = JSON.parse(raw);
  if (!spec || typeof spec !== "object" || !spec.paths) {
    throw new Error("invalid OpenAPI document: missing paths");
  }
  return spec;
}

function pathToRegExp(openapiPath) {
  // Convert /pets/{id} to regex with named-ish capture by index.
  const parts = openapiPath.split("/");
  const regexParts = parts.map((part) => {
    if (part.startsWith("{") && part.endsWith("}")) {
      return "([^/]+)";
    }
    return part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  });
  return new RegExp("^" + regexParts.join("/") + "$");
}

export function matchPath(spec, requestPath) {
  for (const openapiPath of Object.keys(spec.paths)) {
    if (pathToRegExp(openapiPath).test(requestPath)) {
      return openapiPath;
    }
  }
  return null;
}

export function extractParams(openapiPath, requestPath) {
  const partsA = openapiPath.split("/");
  const partsB = requestPath.split("/");
  const params = {};
  for (let i = 0; i < partsA.length; i++) {
    if (partsA[i].startsWith("{") && partsA[i].endsWith("}")) {
      params[partsA[i].slice(1, -1)] = decodeURIComponent(partsB[i]);
    }
  }
  return params;
}

function schemaDefault(schema, spec) {
  if (!schema) return null;
  if (schema.example !== undefined) return schema.example;
  if (Array.isArray(schema.examples) && schema.examples.length) return schema.examples[0];
  if (schema.enum && schema.enum.length) return schema.enum[0];
  if (schema.default !== undefined) return schema.default;
  // resolve $ref
  if (schema.$ref) {
    const name = schema.$ref.split("/").pop();
    const resolved = spec.components?.schemas?.[name];
    if (resolved) return schemaDefault(resolved, spec);
  }
  switch (schema.type) {
    case "string":
      if (schema.format === "date-time") return "2026-01-01T00:00:00Z";
      if (schema.format === "date") return "2026-01-01";
      if (schema.format === "uuid") return "00000000-0000-0000-0000-000000000000";
      return "string";
    case "integer":
    case "number":
      return 0;
    case "boolean":
      return false;
    case "array":
      if (schema.items) return [schemaDefault(schema.items, spec)];
      return [];
    case "object":
      if (schema.properties) {
        const out = {};
        for (const [key, val] of Object.entries(schema.properties)) {
          out[key] = schemaDefault(val, spec);
        }
        return out;
      }
      return {};
    default:
      // infer from properties
      if (schema.properties) {
        const out = {};
        for (const [key, val] of Object.entries(schema.properties)) {
          out[key] = schemaDefault(val, spec);
        }
        return out;
      }
      return null;
  }
}

function pickExample(mediaObj, spec) {
  if (!mediaObj || typeof mediaObj !== "object") return undefined;
  if (mediaObj.example !== undefined) return mediaObj.example;
  if (mediaObj.examples && typeof mediaObj.examples === "object") {
    const firstKey = Object.keys(mediaObj.examples)[0];
    const ex = mediaObj.examples[firstKey];
    if (ex && ex.value !== undefined) return ex.value;
    if (ex !== undefined) return ex;
  }
  if (mediaObj.schema) {
    // schema.example
    if (mediaObj.schema.example !== undefined) return mediaObj.schema.example;
    return schemaDefault(mediaObj.schema, spec);
  }
  return undefined;
}

export function buildResponse(spec, openapiPath, method, params) {
  const pathItem = spec.paths[openapiPath];
  const operation = pathItem?.[method.toLowerCase()];
  if (!operation) return null; // unknown method

  // required parameter validation
  const errors = [];
  const parameters = [...(pathItem.parameters || []), ...(operation.parameters || [])];
  for (const p of parameters) {
    if (p.required) {
      let value;
      if (p.in === "path") value = params[p.name];
      else if (p.in === "query") value = null; // query not parsed here; handled by caller? We'll validate in server
      if (p.required && (value === undefined || value === null || value === "")) {
        errors.push({ name: p.name, in: p.in, message: "required" });
      }
    }
  }

  // determine status code
  const responses = operation.responses || {};
  const statusCodes = Object.keys(responses);
  const successCode = statusCodes.find((c) => /^2\d\d$/.test(c)) || statusCodes.find((c) => c === "default") || statusCodes[0] || "200";

  const responseObj = responses[successCode] || {};
  const content = responseObj.content || {};
  const mediaType = content["application/json"] || content[Object.keys(content)[0]];
  let body = pickExample(mediaType, spec);
  if (body === undefined) body = null;

  return { status: Number(successCode) || 200, body, errors, allow: Object.keys(pathItem).filter((k) => ["get","post","put","patch","delete","head","options"].includes(k)).map((m) => m.toUpperCase()) };
}

export function listPaths(spec) {
  return Object.keys(spec.paths);
}

export function validateQuery(spec, openapiPath, method, searchParams) {
  const pathItem = spec.paths[openapiPath];
  const operation = pathItem?.[method.toLowerCase()];
  const errors = [];
  const parameters = [...(pathItem.parameters || []), ...(operation?.parameters || [])];
  for (const p of parameters) {
    if (p.in === "query" && p.required) {
      const v = searchParams.get(p.name);
      if (v === null || v === "") {
        errors.push({ name: p.name, in: "query", message: "required" });
      }
    }
  }
  return errors;
}