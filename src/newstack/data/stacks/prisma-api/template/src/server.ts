import { createDb } from './db';
import { buildApp } from './app';

const PORT = Number(process.env.PORT ?? 5467);
const HOST = process.env.HOST ?? '127.0.0.1';
const db = createDb();

buildApp(db).listen(PORT, HOST, () => {
  console.log(`notes api listening on http://${HOST}:${PORT}`);
});
