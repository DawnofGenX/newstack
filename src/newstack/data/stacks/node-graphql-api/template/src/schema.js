import { allNotes, addNote, resetNotes } from './store.js';

export const typeDefs = /* GraphQL */ `
  type Note {
    id: ID!
    title: String!
    body: String!
  }

  type Query {
    notes: [Note!]!
  }

  type Mutation {
    addNote(title: String!, body: String): Note!
  }
`;

export const resolvers = {
  Query: {
    notes: () => allNotes(),
  },
  Mutation: {
    addNote: (_parent, args) => addNote(args.title, args.body ?? ''),
  },
};

export { resetNotes };