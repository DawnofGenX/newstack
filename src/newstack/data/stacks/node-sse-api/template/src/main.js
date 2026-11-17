import { createServer } from "./server.js";

const port = Number(process.env.PORT ?? 8080);
const host = process.env.HOST ?? "127.0.0.1";
const heartbeatMs = Number(process.env.SSE_HEARTBEAT_MS ?? 15000);

const server = createServer({ heartbeatMs });

server.listen(port, host, () => {
  console.log(`listening on http://${host}:${server.address().port}`);
  console.log(`  curl -N http://${host}:${server.address().port}/events`);
});

// Open streams are connections, so `server.close()` alone waits forever for
// clients that are deliberately not closing. Drop them, then exit.
function shutdown(signal) {
  console.log(`${signal}: closing ${server.hub.size} stream(s)`);
  server.hub.close();
  server.close(() => process.exit(0));
  server.closeAllConnections?.();
  setTimeout(() => process.exit(0), 2000).unref();
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
