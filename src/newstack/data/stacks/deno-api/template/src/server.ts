import { handler } from "./handler.ts";

const port = Number(Deno.env.get("PORT") ?? 8080);
const hostname = Deno.env.get("ADDR") ?? "127.0.0.1";

const server = Deno.serve({ port, hostname }, handler);

console.log(`listening on http://${hostname}:${server.addr.port}`);

// Stop accepting connections and let in-flight requests finish, so a supervisor
// (or a CI step) that sends SIGTERM sees a clean exit rather than a kill.
for (const signal of ["SIGINT", "SIGTERM"] as const) {
  Deno.addSignalListener(signal, () => {
    server.shutdown();
    Deno.exit(0);
  });
}
