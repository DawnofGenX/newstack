import { createApp } from "./server.js";

const port = Number(process.env.PORT ?? 8080);
const host = process.env.HOST ?? "127.0.0.1";

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  console.error(`PORT must be a port number, got ${process.env.PORT}`);
  process.exit(2);
}

const { server, sockets } = createApp();

server.listen(port, host, () => {
  const address = server.address();
  console.log(`blog-count-ws listening on ws://${address.address}:${address.port}/ws`);
});

// A container sends SIGTERM; close the sockets first so no client sees a reset.
function stop(signal) {
  console.log(`${signal} received, closing ${sockets.clients.size} client(s)`);
  for (const client of sockets.clients) client.close(1001, "server shutting down");
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(0), 2000).unref();
}

process.on("SIGTERM", () => stop("SIGTERM"));
process.on("SIGINT", () => stop("SIGINT"));
