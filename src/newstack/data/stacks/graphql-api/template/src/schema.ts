/**
 * The schema is a string, not a `.graphql` file, on purpose: the build is plain `tsc`, and
 * importing an SDL file would need a bundler or a loader. Keeping it here also keeps the
 * schema next to the resolvers that have to satisfy it.
 */
export const typeDefs = /* GraphQL */ `
  """
  A word/line/byte count. Counts follow \`wc\`: lines are newlines, words are maximal runs
  of non-whitespace, and bytes are the UTF-8 encoding rather than characters.
  """
  type Stat {
    text: String!
    lines: Int!
    words: Int!
    bytes: Int!
  }

  type Health {
    status: String!
  }

  type Query {
    "Readiness probe. Always \`{ status: \\"ok\\" }\` while the server is up."
    health: Health!
    "Count the text given in \`text\`. Blank text is a legitimate zero, absent text is an error."
    stats(text: String!): Stat!
  }
`;
