import http2 from "node:http2";

import { createApp } from "./app.js";

export function createServer(options = {}) {
  const app = createApp(options);
  // `createServer(options, handler)` installs the HTTP/1-compatible request/response
  // pair; the raw `Http2Stream` lives on the `stream` event, which is what the app
  // needs in order to answer every route itself.
  const server = http2.createServer({
    settings: {
      maxConcurrentStreams: 64,
      initialWindowSize: 1 << 20,
    },
  });
  server.on("stream", (stream, headers) => {
    app.handle(stream, headers);
  });
  server.on("session", (session) => {
    session.on("error", () => {});
    session.setTimeout(30_000, () => session.close());
  });
  return { server, app };
}

export function listen(server, host, port) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, host, () => {
      server.off("error", reject);
      resolve(server.address());
    });
  });
}

export function stop(server) {
  return new Promise((resolve) => {
    server.close(() => resolve());
    server.closeIdleConnections?.();
    setTimeout(() => {
      server.closeAllConnections?.();
      resolve();
    }, 2_000).unref();
  });
}
