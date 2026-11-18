import { serve } from "@hono/node-server";
import { app } from "./app.js";

const port = Number(process.env.PORT || 5560);
serve({ fetch: app.fetch, port }, (info) => {
  console.log(`listening on ${info.port}`);
});