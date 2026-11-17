import { createServer as createHttpServer } from "node:http";
import { URL } from "node:url";
import * as O from "./openapi.js";

export function createServer({ spec }) {
  const allowedPaths = O.listPaths(spec);

  async function handle(req, res) {
    const url = new URL(req.url ?? "/", "http://127.0.0.1");
    const method = (req.method || "GET").toUpperCase();
    const openapiPath = O.matchPath(spec, url.pathname);

    if (!openapiPath) {
      const body = JSON.stringify({ error: "not_found", paths: allowedPaths });
      res.writeHead(404, { "content-type": "application/json; charset=utf-8", "content-length": Buffer.byteLength(body) });
      res.end(body);
      return;
    }

    const pathItem = spec.paths[openapiPath];
    const op = pathItem?.[method.toLowerCase()];
    if (!op) {
      const allow = Object.keys(pathItem).filter((k) => ["get","post","put","patch","delete","head","options"].includes(k)).map((m) => m.toUpperCase());
      const body = JSON.stringify({ error: "method_not_allowed", allow });
      res.writeHead(405, { "content-type": "application/json; charset=utf-8", "content-length": Buffer.byteLength(body), allow: allow.join(", ") });
      res.end(body);
      return;
    }

    const params = O.extractParams(openapiPath, url.pathname);
    const queryErrors = O.validateQuery(spec, openapiPath, method, url.searchParams);
    // path param required validation
    const pathErrors = [];
    const paramsDef = [...(pathItem.parameters || []), ...(op.parameters || [])];
    for (const p of paramsDef) {
      if (p.in === "path" && p.required) {
        if (params[p.name] === undefined || params[p.name] === "") {
          pathErrors.push({ name: p.name, in: "path", message: "required" });
        }
      }
    }
    const errors = [...queryErrors, ...pathErrors];
    if (errors.length) {
      const body = JSON.stringify({ error: "validation_error", details: errors });
      res.writeHead(400, { "content-type": "application/json; charset=utf-8", "content-length": Buffer.byteLength(body) });
      res.end(body);
      return;
    }

    const built = O.buildResponse(spec, openapiPath, method, params);
    const body = JSON.stringify(built.body);
    res.writeHead(built.status, { "content-type": "application/json; charset=utf-8", "content-length": Buffer.byteLength(body) });
    res.end(body);
  }

  const server = createHttpServer((req, res) => {
    handle(req, res).catch((err) => {
      if (res.headersSent) { res.destroy(); return; }
      const body = JSON.stringify({ error: "internal", detail: err.message });
      res.writeHead(500, { "content-type": "application/json; charset=utf-8" });
      res.end(body);
    });
  });
  server.spec = spec;
  return server;
}