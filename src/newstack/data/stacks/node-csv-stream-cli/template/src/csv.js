import { Transform } from "node:stream";

export function parseRecord(text, flush) {
  if (text === "" && !flush) return null;
  // An empty buffer at EOF produces no record.
  if (text === "" && flush) return null;
  let i = 0;
  const fields = [];
  let field = "";
  let inQuotes = false;
  let fieldStarted = false;

  while (i < text.length) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i += 2;
          continue;
        }
        inQuotes = false;
        i += 1;
        continue;
      }
      field += c;
      i += 1;
      continue;
    }
    if (c === '"') {
      if (field === "" && !fieldStarted) {
        inQuotes = true;
        i += 1;
        fieldStarted = true;
        continue;
      }
      field += c;
      i += 1;
      fieldStarted = true;
      continue;
    }
    if (c === ",") {
      fields.push(field);
      field = "";
      fieldStarted = false;
      i += 1;
      continue;
    }
    if (c === "\n") {
      fields.push(field);
      return { row: fields, consumed: i + 1 };
    }
    if (c === "\r") {
      if (text[i + 1] === "\n") {
        fields.push(field);
        return { row: fields, consumed: i + 2 };
      }
      field += c;
      i += 1;
      fieldStarted = true;
      continue;
    }
    field += c;
    i += 1;
    fieldStarted = true;
  }

  if (!flush) return null;
  fields.push(field);
  return { row: fields, consumed: text.length };
}

export class CsvParser extends Transform {
  constructor() {
    super({ readableObjectMode: true });
    this.buffer = "";
  }
  _transform(chunk, _enc, cb) {
    this.buffer += typeof chunk === "string" ? chunk : chunk.toString("utf8");
    let rec;
    while ((rec = parseRecord(this.buffer, false)) !== null) {
      this.push(rec.row);
      this.buffer = this.buffer.slice(rec.consumed);
    }
    cb();
  }
  _flush(cb) {
    let rec;
    while (this.buffer.length > 0) {
      rec = parseRecord(this.buffer, true);
      if (!rec) break;
      this.push(rec.row);
      this.buffer = this.buffer.slice(rec.consumed);
      if (rec.consumed === 0) break;
    }
    cb();
  }
}

export function encodeField(value) {
  const s = value == null ? "" : String(value);
  if (/[",\r\n]/.test(s)) return '"' + s.replace(/"/g, '""') + '"';
  return s;
}

export function encodeRow(row) {
  return row.map(encodeField).join(",") + "\r\n";
}

export class CsvSerializer extends Transform {
  constructor() {
    super({ writableObjectMode: true });
    this.headerWritten = false;
  }
  _transform(chunk, _enc, cb) {
    if (Array.isArray(chunk)) {
      this.push(encodeRow(chunk));
    } else if (chunk && typeof chunk === "object") {
      if (!this.headerWritten) {
        this.push(encodeRow(Object.keys(chunk)));
        this.headerWritten = true;
      }
      this.push(encodeRow(Object.keys(chunk).map((k) => chunk[k])));
    }
    cb();
  }
  _flush(cb) { cb(); }
}

export async function parseStream(stream) {
  const parser = new CsvParser();
  stream.pipe(parser);
  const rows = [];
  for await (const row of parser) rows.push(row);
  return rows;
}

export function rowsToObjects(rows) {
  if (rows.length === 0) return [];
  const header = rows[0];
  return rows.slice(1).map((r) => {
    const o = {};
    header.forEach((h, idx) => { o[h] = r[idx] ?? ""; });
    return o;
  });
}

export function objectsToCsv(objects) {
  if (objects.length === 0) return "";
  const header = Object.keys(objects[0]);
  let out = encodeRow(header);
  for (const o of objects) out += encodeRow(header.map((h) => o[h]));
  return out;
}