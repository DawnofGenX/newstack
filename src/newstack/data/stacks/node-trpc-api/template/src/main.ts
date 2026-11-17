import http from "node:http";
import { createHTTPServer } from "@trpc/server/adapters/standalone";
import { appRouter } from "./router.js";

const port = Number(process.env.PORT ?? 5511);

const server = createHTTPServer({
  router: appRouter,
  createContext: () => ({}),
});

server.listen(port, () => {
  console.log(`listening on http://127.0.0.1:${port}`);
});