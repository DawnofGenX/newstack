import { createServer } from "node:http";

import { yoga } from "./yoga.js";

const port = Number.parseInt(process.env.PORT ?? "5441", 10);
const server = createServer(yoga);

server.listen(port, "127.0.0.1", () => {
  console.log(`listening on http://127.0.0.1:${port}/graphql`);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => {
    server.close(() => process.exit(0));
  });
}
