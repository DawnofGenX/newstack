import { createServer } from 'node:http';
import { createYoga, createSchema } from 'graphql-yoga';
import { typeDefs, resolvers } from './schema.js';

const port = Number(process.env.PORT || 5551);

const yoga = createYoga({
  schema: createSchema({ typeDefs, resolvers }),
});

const server = createServer(yoga);
server.listen(port, '127.0.0.1', () => {
  console.log(`node-graphql-api listening on http://127.0.0.1:${port}/graphql`);
});