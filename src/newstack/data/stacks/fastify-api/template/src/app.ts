/** Fastify wiring: one catch-all route keeps the routing table in `contract.route`. */
import Fastify, { type FastifyInstance } from "fastify";

import { route } from "./contract.js";

const MAX_BODY = 64 * 1024;

export function createApp(): FastifyInstance {
  const app = Fastify({ logger: false, bodyLimit: MAX_BODY });

  // Everything is parsed as text: `route` needs the raw body to tell malformed
  // JSON from a missing member, and Fastify's own parser would answer 400 first.
  // The built-in JSON parser must go too: it takes precedence over `*` for
  // `application/json`, and then `{}` arrives as an object and looks malformed.
  app.removeAllContentTypeParsers();
  app.addContentTypeParser("*", { parseAs: "string" }, (_request, body, done) => {
    done(null, body);
  });

  app.setErrorHandler((error, _request, reply) => {
    const code = (error as { code?: string }).code ?? "";
    if (code === "FST_ERR_CTP_BODY_TOO_LARGE") {
      void reply.code(413).type("application/json; charset=utf-8").send('{"error":"body_too_large"}');
      return;
    }
    void reply.code(422).type("application/json; charset=utf-8").send('{"error":"invalid_json"}');
  });

  for (const url of ["/", "/*"]) {
    app.all(url, async (request, reply) => {
      const raw = typeof request.body === "string" ? request.body : undefined;
      const answer = route({ method: request.method, target: request.raw.url ?? "/", body: raw });
      // Send a JSON string, not an object: Fastify's serializer would be free to
      // reorder keys, and the contract fixes the order of the stats reply.
      await reply.code(answer.status).type("application/json; charset=utf-8").send(JSON.stringify(answer.body));
    });
  }

  return app;
}
