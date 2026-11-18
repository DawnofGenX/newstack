import { readFileSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';

export function parseCsv(text) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length === 0) return { header: [], rows: [] };
  const parseLine = (line) => {
    const out = [];
    let cur = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (inQuotes) {
        if (ch === '"' && line[i + 1] === '"') { cur += '"'; i++; }
        else if (ch === '"') inQuotes = false;
        else cur += ch;
      } else {
        if (ch === '"') inQuotes = true;
        else if (ch === ',') { out.push(cur); cur = ''; }
        else cur += ch;
      }
    }
    out.push(cur);
    return out;
  };
  const header = parseLine(lines[0]);
  const rows = lines.slice(1).filter(l => l.trim() !== '').map(parseLine);
  return { header, rows };
}

export function importCsv(csvPath, dbPath) {
  const text = readFileSync(csvPath, 'utf8');
  const { header, rows } = parseCsv(text);
  const db = new DatabaseSync(dbPath);
  const cols = header.map((h) => `"${h.replace(/"/g, '""')}" TEXT`).join(', ');
  db.exec(`CREATE TABLE IF NOT EXISTS data (${cols})`);
  db.exec('DELETE FROM data');
  const placeholders = header.map(() => '?').join(', ');
  const stmt = db.prepare(`INSERT INTO data VALUES (${placeholders})`);
  for (const row of rows) {
    stmt.run(...row);
  }
  db.close();
  return { rows: rows.length, columns: header.length };
}

export function runQuery(dbPath, sql) {
  const db = new DatabaseSync(dbPath);
  const stmt = db.prepare(sql);
  let result;
  try {
    result = stmt.all();
  } catch (e) {
    // maybe non-select
    const info = stmt.run();
    db.close();
    return { changes: info.changes, lastInsertRowid: info.lastInsertRowid };
  }
  db.close();
  return result;
}
