import { importCsv, runQuery } from './sqlite.js';

const args = process.argv.slice(2);
const cmd = args[0];

if (cmd === 'import') {
  const csv = args[1];
  const db = args[2];
  if (!csv || !db) { console.error('usage: import <csv> <db>'); process.exit(2); }
  const r = importCsv(csv, db);
  console.log(`imported ${r.rows} rows, ${r.columns} columns`);
} else if (cmd === 'query') {
  const db = args[1];
  const sql = args.slice(2).join(' ');
  if (!db || !sql) { console.error('usage: query <db> <sql>'); process.exit(2); }
  const r = runQuery(db, sql);
  console.log(JSON.stringify(r, null, 2));
} else if (args.includes('--help') || args.includes('-h')) {
  console.log('Usage: sqlite-import import <csv> <db> | query <db> <sql>');
  process.exit(0);
} else {
  console.error('unknown command');
  process.exit(2);
}
