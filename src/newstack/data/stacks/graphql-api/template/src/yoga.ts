import { createSchema, createYoga } from "graphql-yoga";

import { depthLimit } from "./limits.js";
import { resolvers } from "./resolvers.js";
import { typeDefs } from "./schema.js";

/**
 * `createYoga` returns a fetch handler, not a server. Tests call `yoga.fetch()` directly
 * and get a real `Response`, so the suite needs no port and no teardown — but the shipped
 * verify step still boots a socket, because a handler that only works in-process would pass
 * these tests and fail the deploy.
 */
export const schema = createSchema({ typeDefs, resolvers });

export const yoga = createYoga({
  schema,
  graphqlEndpoint: "/graphql",
  plugins: [depthLimit()],
  // The GraphQL playground is a development affordance; the JSON logger is noise in tests.
  graphiql: true,
  logging: false,
  cors: false,
});
