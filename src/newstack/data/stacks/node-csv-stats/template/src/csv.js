// parseCsv understands RFC 4180 quoting: doubled quotes, embedded commas and newlines.
export function parseCsv(text) {
  const src = String(text);
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  let i = 0;
  while (i < src.length) {
    const ch = src[i];
    if (inQuotes) {
      if (ch === '"') {
        if (src[i + 1] === '"') {
          field += '"';
          i += 2;
          continue;
        }
        inQuotes = false;
        i += 1;
        continue;
      }
      field += ch;
      i += 1;
      continue;
    }
    if (ch === '"' && field === "") {
      inQuotes = true;
      i += 1;
      continue;
    }
    if (ch === ",") {
      row.push(field);
      field = "";
      i += 1;
      continue;
    }
    if (ch === "\r") {
      i += 1;
      continue;
    }
    if (ch === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
      i += 1;
      continue;
    }
    field += ch;
    i += 1;
  }
  if (inQuotes) throw new Error("unterminated quoted field");
  if (field !== "" || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  const nonEmpty = rows.filter((r) => !(r.length === 1 && r[0] === ""));
  if (nonEmpty.length === 0) return { headers: [], rows: [] };
  const [headers, ...data] = nonEmpty;
  data.forEach((r, idx) => {
    if (r.length !== headers.length) {
      throw new Error(`row ${idx + 2} has ${r.length} fields, expected ${headers.length}`);
    }
  });
  return { headers, rows: data };
}

function numericSummary(values) {
  const numbers = values.filter((v) => v.trim() !== "" && !Number.isNaN(Number(v))).map(Number);
  if (numbers.length === 0) return null;
  const sum = numbers.reduce((a, b) => a + b, 0);
  return {
    count: numbers.length,
    min: Math.min(...numbers),
    max: Math.max(...numbers),
    mean: Number((sum / numbers.length).toFixed(6)),
  };
}

// summarize reports per column counts plus numeric stats when the column parses.
export function summarize(headers, rows) {
  return headers.map((column, index) => {
    const values = rows.map((r) => r[index] ?? "");
    const present = values.filter((v) => v.trim() !== "").length;
    return {
      column,
      rows: rows.length,
      present,
      empty: rows.length - present,
      distinct: new Set(values.map((v) => v.trim())).size,
      numeric: numericSummary(values),
    };
  });
}
