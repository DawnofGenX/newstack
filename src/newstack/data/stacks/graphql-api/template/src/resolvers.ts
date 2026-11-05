import { GraphQLError } from "graphql";

import { countText, type Counts } from "./stat.js";

export interface Stat extends Counts {
  readonly text: string;
}

export interface StatArgs {
  readonly text: unknown;
}

/**
 * Resolvers stay thin: the counting rules live in `stat.ts`, and the only thing GraphQL
 * adds is the shape a client asked for. A bad argument is a `GraphQLError` with a machine
 * code, not a thrown `TypeError` — a 500 tells the client nothing it can act on.
 */
export const resolvers = {
  Query: {
    health: (): { status: string } => ({ status: "ok" }),
    stats: (_parent: unknown, args: StatArgs): Stat => {
      if (typeof args.text !== "string") {
        throw new GraphQLError("`text` must be a string", {
          extensions: { code: "BAD_USER_INPUT" },
        });
      }

      return { text: args.text, ...countText(args.text) };
    },
  },
};
