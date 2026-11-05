import { handler } from "./handler.ts";

const port = Number(Bun.env.PORT ?? 8080);
const hostname = Bun.env.ADDR ?? "127.0.0.1";

const server = Bun.serve({ port, hostname, fetch: handler });

console.log(`listening on http://${server.hostname}:${server.port}`);

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.on(signal, () => {
    server.stop(true);
    process.exit(0);
  });
}
