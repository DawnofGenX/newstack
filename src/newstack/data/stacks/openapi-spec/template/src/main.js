import { createHttpServer } from "./server.js";

const port = Number.parseInt(process.env.PORT ?? "5399", 10);
const server = createHttpServer();

server.listen(port, "127.0.0.1", () => {
  console.log(`listening on http://127.0.0.1:${port}`);
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.on(signal, () => {
    server.close(() => process.exit(0));
  });
}
