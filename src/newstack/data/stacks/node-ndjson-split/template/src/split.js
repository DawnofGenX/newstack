export function parseNdjson(text) {
  const records = [];
  const lines = String(text).split(/\r?\n/);
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i].trim();
    if (!line) continue;
    try {
      records.push(JSON.parse(line));
    } catch (err) {
      throw new Error(`invalid json on line ${i + 1}: ${err.message}`);
    }
  }
  return records;
}

export function serialize(records) {
  if (records.length === 0) return "";
  return records.map((r) => JSON.stringify(r)).join("\n") + "\n";
}

function lineSize(record) {
  return Buffer.byteLength(JSON.stringify(record) + "\n", "utf8");
}

export function splitRecords(records, { maxLines = Infinity, maxBytes = Infinity } = {}) {
  if (!(maxLines > 0) && maxLines !== Infinity) throw new Error("maxLines must be positive");
  if (!(maxBytes > 0) && maxBytes !== Infinity) throw new Error("maxBytes must be positive");
  const chunks = [];
  let current = [];
  let bytes = 0;
  for (const record of records) {
    const size = lineSize(record);
    if (size > maxBytes) {
      throw new Error(`single record exceeds maxBytes (${size} > ${maxBytes})`);
    }
    const wouldOverflow = current.length > 0 && (current.length + 1 > maxLines || bytes + size > maxBytes);
    if (wouldOverflow) {
      chunks.push(current);
      current = [];
      bytes = 0;
    }
    current.push(record);
    bytes += size;
  }
  if (current.length > 0) chunks.push(current);
  return chunks;
}

export function partName(index) {
  return `part-${String(index).padStart(4, "0")}.ndjson`;
}
