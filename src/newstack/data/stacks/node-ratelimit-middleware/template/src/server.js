import http from "node:http";
import { createLimiter } from "./limiter.js";

const PORT = process.env.PORT ? Number(process.env.PORT) : 5590;
const LIMIT = process.env.RATE_LIMIT ? Number(process.env.RATE_LIMIT) : 10;
const WINDOW_MS = process.env.RATE_WINDOW_MS
  ? Number(process.env.RATE_WINDOW_MS)
  : 60000;

const limiter = createLimiter({ limit: LIMIT, windowMs: WINDOW_MS });

const server = http.createServer((req, res) => {
  if (req.url === "/stats") {
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify(limiter.stats()));
    return;
  }
  const result = limiter.tryAcquire();
  if (!result.allowed) {
    res.statusCode = 429;
    res.setHeader("Retry-After", String(result.retryAfter));
    res.end("Too Many Requests");
    return;
  }
  res.statusCode = 200;
  res.end("ok");
});

server.listen(PORT, () => {
  process.stdout.write(`listening on ${PORT}\n`);
});

export { server, limiter };
