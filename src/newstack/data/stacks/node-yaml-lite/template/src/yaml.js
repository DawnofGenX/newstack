/** A dependency-free YAML subset: block maps, sequences, flow collections. */
export class YamlError extends Error {
  constructor(message) {
    super(message);
    this.name = "YamlError";
  }
}

const NUMBER = /^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][-+]?\d+)?$/;

function stripComment(line) {
  let quote = null;
  for (let index = 0; index < line.length; index++) {
    const char = line[index];
    if (quote) {
      if (char === quote) {
        quote = null;
      }
      continue;
    }
    if (char === '"' || char === "'") {
      quote = char;
      continue;
    }
    if (char === "#" && (index === 0 || line[index - 1] === " " || line[index - 1] === "\t")) {
      return line.slice(0, index);
    }
  }
  return line;
}

function unquote(text, line) {
  const quote = text[0];
  const body = text.slice(1);
  let out = "";
  for (let index = 0; index < body.length; index++) {
    const char = body[index];
    if (char === quote) {
      if (quote === "'" && body[index + 1] === "'") {
        out += "'";
        index++;
        continue;
      }
      const rest = body.slice(index + 1).trim();
      if (rest !== "") {
        throw new YamlError(`line ${line}: unexpected text after a quoted scalar: ${rest}`);
      }
      if (quote === '"') {
        return JSON.parse(`"${out.replace(/"/g, '\\"')}"`);
      }
      return out;
    }
    out += char;
  }
  throw new YamlError(`line ${line}: unterminated quoted scalar`);
}

/** Parses a scalar, including the `[...]` and `{...}` flow forms. */
export function parseScalar(text, line = 0) {
  const value = text.trim();
  if (value === "") {
    return null;
  }
  if (value.startsWith('"') || value.startsWith("'")) {
    return unquote(value, line);
  }
  if (value.startsWith("[")) {
    return parseFlow(value, line).value;
  }
  if (value.startsWith("{")) {
    return parseFlow(value, line).value;
  }
  if (value === "null" || value === "~") {
    return null;
  }
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  if (NUMBER.test(value)) {
    return Number(value);
  }
  if (/^[|>]/.test(value)) {
    throw new YamlError(`line ${line}: block scalars (| and >) are not supported`);
  }
  return value;
}

function parseFlow(text, line) {
  let index = 0;

  const skipSpace = () => {
    while (index < text.length && /\s/.test(text[index])) {
      index++;
    }
  };

  const fail = (message) => {
    throw new YamlError(`line ${line}: ${message}`);
  };

  const readScalarToken = () => {
    const start = index;
    while (index < text.length && !",]}".includes(text[index])) {
      index++;
    }
    return parseScalar(text.slice(start, index), line);
  };

  const readKey = () => {
    if (text[index] === '"' || text[index] === "'") {
      const quote = text[index];
      let end = index + 1;
      let out = "";
      while (end < text.length) {
        if (text[end] === quote) {
          break;
        }
        out += text[end];
        end++;
      }
      if (text[end] !== quote) {
        fail("unterminated quoted key");
      }
      index = end + 1;
      return out;
    }
    const start = index;
    while (index < text.length && text[index] !== ":") {
      index++;
    }
    return text.slice(start, index).trim();
  };

  const parseValue = () => {
    skipSpace();
    const char = text[index];
    if (char === "[") {
      index++;
      const items = [];
      skipSpace();
      if (text[index] === "]") {
        index++;
        return items;
      }
      for (;;) {
        items.push(parseValue());
        skipSpace();
        if (text[index] === ",") {
          index++;
          continue;
        }
        if (text[index] === "]") {
          index++;
          return items;
        }
        fail("expected , or ] in a flow sequence");
      }
    }
    if (char === "{") {
      index++;
      const map = {};
      skipSpace();
      if (text[index] === "}") {
        index++;
        return map;
      }
      for (;;) {
        skipSpace();
        const key = readKey();
        if (key === "") {
          fail("empty key in a flow mapping");
        }
        if (text[index] !== ":") {
          fail(`expected : after the key ${key}`);
        }
        index++;
        map[key] = parseValue();
        skipSpace();
        if (text[index] === ",") {
          index++;
          continue;
        }
        if (text[index] === "}") {
          index++;
          return map;
        }
        fail("expected , or } in a flow mapping");
      }
    }
    return readScalarToken();
  };

  const value = parseValue();
  skipSpace();
  if (index !== text.length) {
    fail(`unexpected trailing text: ${text.slice(index)}`);
  }
  return { value };
}

/** Parses YAML text into plain JavaScript values. */
export function parseYaml(source) {
  const lines = [];
  source.split(/\r?\n/).forEach((raw, index) => {
    const indentText = raw.slice(0, raw.length - raw.trimStart().length);
    if (indentText.includes("\t")) {
      throw new YamlError(`line ${index + 1}: tabs are not allowed for indentation`);
    }
    const text = stripComment(raw).replace(/\s+$/, "");
    const trimmed = text.trim();
    if (trimmed === "" || trimmed === "---" || trimmed === "...") {
      return;
    }
    lines.push({ indent: text.length - text.trimStart().length, text: trimmed, line: index + 1 });
  });
  if (lines.length === 0) {
    return null;
  }

  const parser = { lines, pos: 0 };

  const isSequenceItem = (entry) => entry.text === "-" || entry.text.startsWith("- ");

  const splitKey = (entry) => {
    let quote = null;
    for (let index = 0; index < entry.text.length; index++) {
      const char = entry.text[index];
      if (quote) {
        if (char === quote) {
          quote = null;
        }
        continue;
      }
      if (char === '"' || char === "'") {
        quote = char;
        continue;
      }
      if (char === ":" && (index + 1 === entry.text.length || entry.text[index + 1] === " ")) {
        const rawKey = entry.text.slice(0, index);
        const key = rawKey.startsWith('"') || rawKey.startsWith("'")
          ? unquote(rawKey.trim(), entry.line)
          : rawKey.trim();
        if (key === "") {
          throw new YamlError(`line ${entry.line}: empty key`);
        }
        return { key, rest: entry.text.slice(index + 1).trim() };
      }
    }
    return null;
  };

  const parseBlock = (indent) => {
    const first = parser.lines[parser.pos];
    if (!first || first.indent < indent) {
      return null;
    }
    return isSequenceItem(first) ? parseSequence(indent) : parseMapping(indent);
  };

  const parseSequence = (indent) => {
    const items = [];
    while (parser.pos < parser.lines.length) {
      const entry = parser.lines[parser.pos];
      if (entry.indent < indent) {
        break;
      }
      if (entry.indent > indent) {
        throw new YamlError(`line ${entry.line}: unexpected indentation in a sequence`);
      }
      if (!isSequenceItem(entry)) {
        break;
      }
      const content = entry.text === "-" ? "" : entry.text.slice(2).trim();
      parser.pos++;
      if (content === "") {
        const next = parser.lines[parser.pos];
        items.push(next && next.indent > indent ? parseBlock(next.indent) : null);
        continue;
      }
      const pair = splitKey({ ...entry, text: content });
      if (pair) {
        const map = {};
        if (pair.rest === "") {
          const next = parser.lines[parser.pos];
          map[pair.key] = next && next.indent > indent ? parseBlock(next.indent) : null;
        } else {
          map[pair.key] = parseScalar(pair.rest, entry.line);
        }
        while (parser.pos < parser.lines.length && parser.lines[parser.pos].indent > indent) {
          Object.assign(map, parseMapping(parser.lines[parser.pos].indent));
        }
        items.push(map);
        continue;
      }
      items.push(parseScalar(content, entry.line));
      const next = parser.lines[parser.pos];
      if (next && next.indent > indent) {
        throw new YamlError(`line ${next.line}: unexpected indentation after a scalar item`);
      }
    }
    return items;
  };

  const parseMapping = (indent) => {
    const map = {};
    while (parser.pos < parser.lines.length) {
      const entry = parser.lines[parser.pos];
      if (entry.indent < indent) {
        break;
      }
      if (entry.indent > indent) {
        throw new YamlError(`line ${entry.line}: unexpected indentation in a mapping`);
      }
      if (isSequenceItem(entry)) {
        break;
      }
      const pair = splitKey(entry);
      if (!pair) {
        throw new YamlError(`line ${entry.line}: expected key: value, got ${entry.text}`);
      }
      if (Object.hasOwn(map, pair.key)) {
        throw new YamlError(`line ${entry.line}: duplicate key ${pair.key}`);
      }
      parser.pos++;
      if (pair.rest === "") {
        const next = parser.lines[parser.pos];
        map[pair.key] = next && next.indent > indent ? parseBlock(next.indent) : null;
      } else {
        map[pair.key] = parseScalar(pair.rest, entry.line);
      }
    }
    return map;
  };

  const value = parseBlock(lines[0].indent);
  if (parser.pos < parser.lines.length) {
    throw new YamlError(`line ${parser.lines[parser.pos].line}: unexpected content`);
  }
  return value;
}

/** Serialises a value as block YAML with two space indentation. */
export function stringifyYaml(value, indent = 0) {
  const pad = " ".repeat(indent);
  if (value === null || value === undefined) {
    return "null";
  }
  if (Array.isArray(value)) {
    if (value.length === 0) {
      return "[]";
    }
    return value
      .map((item) => {
        if (item !== null && typeof item === "object") {
          const nested = stringifyYaml(item, indent + 2);
          return `${pad}-\n${nested}`;
        }
        return `${pad}- ${scalar(item)}`;
      })
      .join("\n");
  }
  if (typeof value === "object") {
    const keys = Object.keys(value);
    if (keys.length === 0) {
      return "{}";
    }
    return keys
      .map((key) => {
        const item = value[key];
        if (item !== null && typeof item === "object") {
          if ((Array.isArray(item) && item.length === 0) || (!Array.isArray(item) && Object.keys(item).length === 0)) {
            return `${pad}${key}: ${Array.isArray(item) ? "[]" : "{}"}`;
          }
          return `${pad}${key}:\n${stringifyYaml(item, indent + 2)}`;
        }
        return `${pad}${key}: ${scalar(item)}`;
      })
      .join("\n");
  }
  return `${pad}${scalar(value)}`;
}

function scalar(value) {
  if (typeof value === "string") {
    const plain = value !== "" &&
      !/^[\s\-?:,[\]{}#&*!|>'"%@`]/.test(value) &&
      !/[:#]\s/.test(value) &&
      !value.endsWith(" ") &&
      !/^(null|~|true|false|-?\d)/.test(value);
    return plain ? value : JSON.stringify(value);
  }
  return String(value);
}

/** Reads a dotted path with optional `[index]` segments. */
export function getPath(value, path) {
  const parts = path.replace(/\[(\d+)\]/g, ".$1").split(".").filter((part) => part !== "");
  let current = value;
  for (const part of parts) {
    if (current === null || typeof current !== "object") {
      return undefined;
    }
    current = current[part];
  }
  return current;
}
