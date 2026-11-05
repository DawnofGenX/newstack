//! A local target with the shapes that break naive load tests.

import http from "node:http";
import { fileURLToPath } from "node:url";

export interface Stub {
  readonly server: http.Server;
  readonly port: number;
  readonly close: () => Promise<void>;
}

export interface StubOptions {
  readonly port?: number;
  /** Every n-th request to /flaky fails with 503. */
  readonly failEvery?: number;
}

export function startStub(options: StubOptions = {}): Promise<Stub> {
  const failEvery = options.failEvery ?? 5;
  let seen = 0;
  const server = http.createServer((request, response) => {
    const url = new URL(request.url ?? "/", "http://127.0.0.1");
    if (url.pathname === "/ok") {
      response.writeHead(200, { "content-type": "text/plain" });
      response.end("ok");
      return;
    }
    if (url.pathname === "/flaky") {
      seen += 1;
      if (seen % failEvery === 0) {
        response.writeHead(503, { "content-type": "text/plain" });
        response.end("unavailable");
        return;
      }
      response.writeHead(200, { "content-type": "text/plain" });
      response.end("ok");
      return;
    }
    if (url.pathname === "/slow") {
      const ms = Number(url.searchParams.get("ms") ?? "10");
      setTimeout(() => {
        response.writeHead(200, { "content-type": "text/plain" });
        response.end("slow");
      }, ms);
      return;
    }
    if (url.pathname === "/drip") {
      response.writeHead(200, { "content-type": "text/plain" });
      const chunks = ["one ", "two ", "three"];
      let index = 0;
      const tick = (): void => {
        const chunk = chunks[index];
        index += 1;
        if (chunk === undefined) {
          response.end();
          return;
        }
        response.write(chunk);
        setTimeout(tick, 2);
      };
      tick();
      return;
    }
    response.writeHead(404, { "content-type": "text/plain" });
    response.end("no route");
  });

  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(options.port ?? 0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address !== null ? address.port : 0;
      resolve({
        server,
        port,
        close: () =>
          new Promise<void>((done, fail) => {
            server.close((error) => (error ? fail(error) : done()));
          }),
      });
    });
  });
}

const invoked = process.argv[1];
if (invoked !== undefined && fileURLToPath(import.meta.url) === invoked) {
  const at = process.argv.indexOf("--port");
  const port = at >= 0 ? Number(process.argv[at + 1] ?? "0") : 0;
  const stub = await startStub({ port });
  process.stdout.write(`stub listening on http://127.0.0.1:${stub.port}\n`);
  const stop = (): void => {
    void stub.close().then(() => process.exit(0));
  };
  process.on("SIGINT", stop);
  process.on("SIGTERM", stop);
}
