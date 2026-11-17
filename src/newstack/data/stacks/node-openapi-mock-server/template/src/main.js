import { createServer } from "./server.js";
import { loadSpec } from "./openapi.js";

const port = Number(process.env.PORT ?? 8080);
const host = process.env.HOST ?? "127.0.0.1";
const specPath = process.env.OPENAPI_PATH ?? process.argv[2] ?? "openapi.json";

const spec = loadSpec(specPath);
const server = createServer({ spec });

server.listen(port, host, () => {
  console.log(`listening on http://${host}:${server.address().port}`);
});

function shutdown() {
  server.close(() => process.exit(0));
  setTimeout(() => process.exit(0), 2000).unref();
}
process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);