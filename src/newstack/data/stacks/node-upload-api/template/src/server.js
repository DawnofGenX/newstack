// The HTTP server: bind, route, and stop on a signal without leaving a listener
// behind.
import http from "node:http";
import { route } from "./routes.js";

export async function createServer(store) {
  const server = http.createServer(route(store));
  // A client that opens a socket and never sends a request must not hold a
  // connection forever.
  server.headersTimeout = 10_000;
  server.requestTimeout = 30_000;
  return server;
}

export function listen(server, host, port) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, host, () => {
      server.removeListener("error", reject);
      resolve(server.address().port);
    });
  });
}

export function stop(server) {
  return new Promise((resolve) => {
    server.close(() => resolve());
    // close() waits for keep-alive connections to drain on their own, which can
    // be minutes. Ask idle sockets to go away now, and unref the timer so a
    // process with nothing else to do is not held open by it.
    server.closeIdleConnections();
    const timer = setTimeout(() => server.closeAllConnections(), 2000);
    timer.unref();
  });
}
