/**
 * A TOML reader for the subset that configuration files actually use: bare and
 * quoted keys, dotted keys, `[tables]`, `[[arrays of tables]]`, strings with
 * escapes, integers (decimal, 0x, 0o, 0b, with `_` separators), floats,
 * booleans, arrays and inline tables.
 *
 * Dates are refused rather than guessed at: `1979-05-27T07:32:00Z` looks like a
 * string, a number and a subtraction all at once, and silently picking one is
 * worse than an error that says so.
 */

export type TomlValue = string | number | boolean | TomlValue[] | TomlTable;
export interface TomlTable {
  [key: string]: TomlValue;
}

/** Thrown for anything the reader cannot accept, always with a line number. */
export class TomlError extends Error {
  constructor(
    message: string,
    readonly line: number,
  ) {
    super(`line ${line}: ${message}`);
    this.name = "TomlError";
  }
}

const BARE_KEY = /[A-Za-z0-9_-]/;

class Parser {
  private pos = 0;
  private readonly src: string;

  constructor(source: string) {
    this.src = source;
  }

  private line(): number {
    let count = 1;
    for (let i = 0; i < this.pos && i < this.src.length; i += 1) {
      if (this.src[i] === "\n") count += 1;
    }
    return count;
  }

  private error(message: string): never {
    throw new TomlError(message, this.line());
  }

  private peek(offset = 0): string {
    return this.src[this.pos + offset] ?? "";
  }

  private atEnd(): boolean {
    return this.pos >= this.src.length;
  }

  /** Skips spaces, tabs and newlines. */
  private skipSpace(): void {
    while (!this.atEnd() && (this.peek() === " " || this.peek() === "\t" || this.peek() === "\n" || this.peek() === "\r")) {
      this.pos += 1;
    }
  }

  /** Skips a comment, then whatever whitespace follows it (including newlines). */
  private skipComment(): void {
    if (this.peek() !== "#") return;
    while (!this.atEnd() && this.peek() !== "\n") this.pos += 1;
  }

  private skipTrivia(allowNewlines: boolean): void {
    for (;;) {
      if (this.peek() === "#") {
        this.skipComment();
        continue;
      }
      if (this.peek() === " " || this.peek() === "\t") {
        this.pos += 1;
        continue;
      }
      if (allowNewlines && (this.peek() === "\n" || this.peek() === "\r")) {
        this.pos += 1;
        continue;
      }
      return;
    }
  }

  parse(): TomlTable {
    const root: TomlTable = {};
    let table: TomlTable = root;

    for (;;) {
      this.skipTrivia(true);
      if (this.atEnd()) break;

      if (this.peek() === "[") {
        const isArray = this.peek(1) === "[";
        this.pos += isArray ? 2 : 1;
        this.skipTrivia(false);
        const path = this.readKeyPath();
        this.skipTrivia(false);
        const closer = isArray ? "]]" : "]";
        if (!this.src.startsWith(closer, this.pos)) this.error(`expected '${closer}' to close the table header`);
        this.pos += closer.length;
        table = isArray ? this.arrayTable(root, path) : this.table(root, path);
        this.skipTrivia(false);
        if (!this.atEnd() && this.peek() !== "\n") this.error("unexpected text after the table header");
        continue;
      }

      this.readKeyValueInto(table);
      this.skipTrivia(false);
      if (!this.atEnd() && this.peek() !== "\n") this.error("unexpected text after the value");
    }

    return root;
  }

  private readKeyPath(): string[] {
    const path: string[] = [];
    for (;;) {
      path.push(this.readKey());
      this.skipTrivia(false);
      if (this.peek() !== ".") return path;
      this.pos += 1;
      this.skipTrivia(false);
    }
  }

  private readKey(): string {
    const quote = this.peek();
    if (quote === '"' || quote === "'") return this.readString();
    const start = this.pos;
    while (!this.atEnd() && BARE_KEY.test(this.peek())) this.pos += 1;
    if (this.pos === start) this.error("expected a key");
    return this.src.slice(start, this.pos);
  }

  private descend(base: TomlTable, path: string[]): TomlTable {
    let node: TomlTable = base;
    for (const part of path) {
      const existing = node[part];
      if (existing === undefined) {
        const created: TomlTable = {};
        node[part] = created;
        node = created;
      } else if (Array.isArray(existing)) {
        node = existing[existing.length - 1] as TomlTable;
      } else if (typeof existing === "object" && existing !== null) {
        node = existing;
      } else {
        this.error(`'${part}' is already a value, not a table`);
      }
    }
    return node;
  }

  private table(root: TomlTable, path: string[]): TomlTable {
    const parent = this.descend(root, path.slice(0, -1));
    const name = path[path.length - 1];
    const existing = parent[name];
    if (existing === undefined) {
      const created: TomlTable = {};
      parent[name] = created;
      return created;
    }
    if (Array.isArray(existing) || typeof existing !== "object" || existing === null) {
      this.error(`'${name}' is already a value, not a table`);
    }
    return existing as TomlTable;
  }

  private arrayTable(root: TomlTable, path: string[]): TomlTable {
    const parent = this.descend(root, path.slice(0, -1));
    const name = path[path.length - 1];
    const existing = parent[name];
    const entry: TomlTable = {};
    if (existing === undefined) {
      parent[name] = [entry];
      return entry;
    }
    if (!Array.isArray(existing)) this.error(`'${name}' is already a table, not an array of tables`);
    existing.push(entry);
    return entry;
  }

  private readKeyValueInto(table: TomlTable): void {
    const path = this.readKeyPath();
    this.skipTrivia(false);
    if (this.peek() !== "=") this.error("expected '=' after the key");
    this.pos += 1;
    this.skipTrivia(false);
    const value = this.readValue();
    const target = path.length > 1 ? this.descend(table, path.slice(0, -1)) : table;
    const name = path[path.length - 1];
    if (target[name] !== undefined) this.error(`'${path.join(".")}' is already defined`);
    target[name] = value;
  }

  readValue(): TomlValue {
    const char = this.peek();
    if (char === '"' || char === "'") return this.readString();
    if (char === "[") return this.readArray();
    if (char === "{") return this.readInlineTable();
    return this.readScalar();
  }

  private readArray(): TomlValue[] {
    this.pos += 1;
    const values: TomlValue[] = [];
    for (;;) {
      this.skipTrivia(true);
      if (this.atEnd()) this.error("unterminated array");
      if (this.peek() === "]") {
        this.pos += 1;
        return values;
      }
      values.push(this.readValue());
      this.skipTrivia(true);
      if (this.peek() === ",") {
        this.pos += 1;
        continue;
      }
      if (this.peek() === "]") {
        this.pos += 1;
        return values;
      }
      this.error("expected ',' or ']' in the array");
    }
  }

  private readInlineTable(): TomlTable {
    this.pos += 1;
    const table: TomlTable = {};
    this.skipTrivia(false);
    if (this.peek() === "}") {
      this.pos += 1;
      return table;
    }
    for (;;) {
      this.skipTrivia(false);
      this.readKeyValueInto(table);
      this.skipTrivia(false);
      if (this.peek() === ",") {
        this.pos += 1;
        continue;
      }
      if (this.peek() === "}") {
        this.pos += 1;
        return table;
      }
      this.error("expected ',' or '}' in the inline table");
    }
  }

  private readString(): string {
    const quote = this.peek();
    this.pos += 1;
    let out = "";
    for (;;) {
      if (this.atEnd()) this.error(quote === '"' ? 'unterminated "' : "unterminated '");
      const char = this.peek();
      if (char === quote) {
        this.pos += 1;
        return out;
      }
      if (char === "\n" && quote === "'") this.error("a literal string cannot span lines");
      if (char === "\n") this.error('unterminated "');
      if (char === "\\" && quote === '"') {
        out += this.readEscape();
        continue;
      }
      out += char;
      this.pos += 1;
    }
  }

  private readEscape(): string {
    this.pos += 1;
    const char = this.peek();
    this.pos += 1;
    switch (char) {
      case '"':
        return '"';
      case "\\":
        return "\\";
      case "n":
        return "\n";
      case "t":
        return "\t";
      case "r":
        return "\r";
      case "b":
        return "\b";
      case "f":
        return "\f";
      case "u":
      case "U": {
        const width = char === "u" ? 4 : 8;
        const hex = this.src.slice(this.pos, this.pos + width);
        if (hex.length !== width || !/^[0-9a-fA-F]+$/.test(hex)) this.error("bad unicode escape");
        this.pos += width;
        return String.fromCodePoint(Number.parseInt(hex, 16));
      }
      default:
        this.error(`unknown escape \\${char}`);
    }
  }

  private readScalar(): TomlValue {
    const start = this.pos;
    while (!this.atEnd() && !",]}#".includes(this.peek()) && this.peek() !== " " && this.peek() !== "\t" && this.peek() !== "\n" && this.peek() !== "\r") {
      this.pos += 1;
    }
    const word = this.src.slice(start, this.pos);
    if (word === "") this.error("expected a value");
    if (word === "true") return true;
    if (word === "false") return false;
    if (/^-?\d{4}-\d{2}-\d{2}/.test(word)) this.error("dates are not supported; quote the value if it is text");

    const normalised = word.replace(/_/g, "");
    const radix = /^[+-]?0x/.test(normalised) ? 16 : /^[+-]?0o/.test(normalised) ? 8 : /^[+-]?0b/.test(normalised) ? 2 : 10;
    if (radix !== 10) {
      if (radix === 16 && !/^[+-]?0x[0-9a-fA-F]+$/.test(normalised)) this.error(`not a value: ${word}`);
      if (radix === 8 && !/^[+-]?0o[0-7]+$/.test(normalised)) this.error(`not a value: ${word}`);
      if (radix === 2 && !/^[+-]?0b[01]+$/.test(normalised)) this.error(`not a value: ${word}`);
      const negative = normalised.startsWith("-");
      const digits = normalised.slice(negative ? 3 : 2);
      const value = Number.parseInt(digits, radix);
      return negative ? -value : value;
    }
    if (/^[+-]?\d+$/.test(normalised)) return Number.parseInt(normalised, 10);
    if (/^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$/.test(normalised)) return Number.parseFloat(normalised);

    this.error(`not a value: ${word}`);
  }
}

/** Parses TOML text into a nested object. */
export function parseToml(text: string): TomlTable {
  return new Parser(text).parse();
}

/** Renders a parsed document as dotted `a.b.c` keys, for grepping and diffing. */
export function flatten(table: TomlTable, prefix = ""): Record<string, TomlValue> {
  const out: Record<string, TomlValue> = {};
  for (const [key, value] of Object.entries(table)) {
    const path = prefix === "" ? key : `${prefix}.${key}`;
    if (Array.isArray(value)) {
      if (value.length > 0 && value.every((item) => typeof item === "object" && item !== null && !Array.isArray(item))) {
        value.forEach((item, index) => Object.assign(out, flatten(item as TomlTable, `${path}[${index}]`)));
      } else {
        out[path] = value;
      }
      continue;
    }
    if (typeof value === "object" && value !== null) {
      Object.assign(out, flatten(value as TomlTable, path));
      continue;
    }
    out[path] = value;
  }
  return out;
}

/** Looks up a dotted path such as `server.ports[0]`. */
export function getPath(table: TomlTable, path: string): TomlValue | undefined {
  const parts = path.split(".").flatMap((chunk) => {
    const match = /^([^\[]+)((?:\[\d+\])*)$/.exec(chunk);
    if (match === null) return [chunk];
    const indexes = [...match[2].matchAll(/\[(\d+)\]/g)].map((hit) => Number(hit[1]));
    return [match[1], ...indexes];
  });

  let node: TomlValue | undefined = table;
  for (const part of parts) {
    if (typeof part === "number") {
      if (!Array.isArray(node)) return undefined;
      node = node[part];
      continue;
    }
    if (typeof node !== "object" || node === null || Array.isArray(node)) return undefined;
    node = node[part];
  }
  return node;
}
