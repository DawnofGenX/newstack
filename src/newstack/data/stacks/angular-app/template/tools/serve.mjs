#!/usr/bin/env node
/**
 * Zero-dependency static server for the built SPA.
 *
 * `ng build` emits a content-hashed bundle into `dist/<project>/browser`; serving
 * that directory with a "find the file or fall back to index.html" rule is all a
 * client-side app needs. Anything that looks like a file (has an extension) but is
 * missing must still answer 404, otherwise a stale bundle URL looks like a page.
 */
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, resolve } from "node:path";

const TYPES = new Map([
  [".html", "text/html; charset=utf-8"],
  [".js", "text/javascript; charset=utf-8"],
  [".mjs", "text/javascript; charset=utf-8"],
  [".css", "text/css; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".svg", "image/svg+xml"],
  [".ico", "image/x-icon"],
  [".png", "image/png"],
  [".woff2", "font/woff2"],
  [".map", "application/json; charset=utf-8"],
]);

const root = resolve(process.argv[2] ?? "dist/app/browser");
const port = Number.parseInt(process.env.PORT ?? "8080", 10);
const host = process.env.HOST ?? "127.0.0.1";

async function resolveFile(pathname) {
  const wanted = normalize(decodeURIComponent(pathname)).replace(/^(\.\.[/\\])+/, "");
  const target = join(root, wanted);
  if (!target.startsWith(root)) return undefined;
  try {
    const info = await stat(target);
    if (info.isFile()) return target;
    if (info.isDirectory()) {
      const index = join(target, "index.html");
      const nested = await stat(index).catch(() => undefined);
      if (nested?.isFile()) return index;
    }
  } catch {
    return undefined;
  }
  return undefined;
}

const server = createServer(async (request, response) => {
  const pathname = new URL(request.url ?? "/", "http://localhost").pathname;
  let file = await resolveFile(pathname);
  const looksLikeFile = extname(pathname) !== "";
  if (file === undefined && !looksLikeFile) file = await resolveFile("/index.html");

  if (file === undefined) {
    response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    response.end(`no such file: ${pathname}\n`);
    return;
  }

  const body = await readFile(file);
  const type = TYPES.get(extname(file)) ?? "application/octet-stream";
  response.writeHead(200, {
    "content-type": type,
    "content-length": String(body.length),
    "cache-control": extname(file) === ".html" ? "no-store" : "public, max-age=60",
  });
  response.end(body);
});

server.listen(port, host, () => {
  process.stdout.write(`serving ${root} on http://${host}:${port}\n`);
});

const stop = () => server.close(() => process.exit(0));
process.on("SIGTERM", stop);
process.on("SIGINT", stop);
