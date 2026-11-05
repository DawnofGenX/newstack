import { handler } from "./handler.ts";

const port = Number(Deno.env.get("PORT") ?? "8080");
const hostname = Deno.env.get("ADDR") ?? "127.0.0.1";

// Deno.serve installs its own SIGINT/SIGTERM handling and drains in-flight requests, so
// there is no server lifecycle to manage by hand — one of the reasons this stack needs no
// framework at all.
Deno.serve({ port, hostname }, handler);
