import { describe, expect, test } from "bun:test";
import { flatten, getPath, parseToml, TomlError } from "../src/toml/toml.ts";

describe("parseToml", () => {
  test("parses scalars of every supported type", () => {
    const doc = parseToml(`
title = "Example"
enabled = true
retries = 3
ratio = 0.25
big = 1_000_000
hex = 0xff
octal = 0o755
binary = 0b1010
`);
    expect(doc).toEqual({
      title: "Example",
      enabled: true,
      retries: 3,
      ratio: 0.25,
      big: 1000000,
      hex: 255,
      octal: 493,
      binary: 10,
    });
  });

  test("parses tables, nested tables and dotted keys", () => {
    const doc = parseToml(`
[server]
host = "localhost"
[server.limits]
rate = 100

[client]
timeout.ms = 250
`);
    expect(doc).toEqual({
      server: { host: "localhost", limits: { rate: 100 } },
      client: { timeout: { ms: 250 } },
    });
  });

  test("parses arrays, trailing commas and comments", () => {
    const doc = parseToml(`
# a leading comment
ports = [
  8001, 8002,   # inline comment
  8003,
]
mixed = ["/usr/bin", '/opt']
`);
    expect(doc).toEqual({ ports: [8001, 8002, 8003], mixed: ["/usr/bin", "/opt"] });
  });

  test("parses an array of tables", () => {
    const doc = parseToml(`
[[bin]]
name = "one"
[[bin]]
name = "two"
level = 2
`);
    expect(doc).toEqual({
      bin: [
        { name: "one" },
        { name: "two", level: 2 },
      ],
    });
  });

  test("parses inline tables", () => {
    const doc = parseToml('owner = { name = "alice", age = 30 }\n');
    expect(doc).toEqual({ owner: { name: "alice", age: 30 } });
  });

  test("decodes escapes in basic strings and leaves literal strings alone", () => {
    const doc = parseToml('a = "tab\\there\\nnext\\u0041"\nb = \'raw \\t text\'\n');
    expect(doc["a"]).toBe("tab\there\nnextA");
    expect(doc["b"]).toBe("raw \\t text");
  });

  test("quoted keys may contain dots and spaces", () => {
    const doc = parseToml('"a.b" = 1\n"with space" = 2\n');
    expect(doc).toEqual({ "a.b": 1, "with space": 2 });
  });

  test("reports the line number of the offending value", () => {
    expect(() => parseToml('ok = 1\nbad = \n')).toThrow(/line 2:/);
  });

  test("refuses duplicate keys", () => {
    expect(() => parseToml("a = 1\na = 2\n")).toThrow(/line 2: 'a' is already defined/);
  });

  test("refuses dates rather than guessing", () => {
    expect(() => parseToml("when = 1979-05-27T07:32:00Z\n")).toThrow(/dates are not supported/);
  });

  test("refuses a table header without its bracket", () => {
    expect(() => parseToml("[server\nhost = 1\n")).toThrow(/expected '\]'/);
  });

  test("accepts an empty document", () => {
    expect(parseToml("")).toEqual({});
    expect(parseToml("# only a comment\n")).toEqual({});
  });
});

describe("flatten", () => {
  test("renders dotted keys and indexes arrays of tables", () => {
    const doc = parseToml(`
[server]
host = "localhost"
ports = [8001, 8002]
[[bin]]
name = "one"
[[bin]]
name = "two"
`);
    expect(flatten(doc)).toEqual({
      "server.host": "localhost",
      "server.ports": [8001, 8002],
      "bin[0].name": "one",
      "bin[1].name": "two",
    });
  });
});

describe("getPath", () => {
  const doc = parseToml(`
[server]
host = "localhost"
ports = [8001, 8002]
[[bin]]
name = "one"
`);

  test("walks tables, array indexes and table arrays", () => {
    expect(getPath(doc, "server.host")).toBe("localhost");
    expect(getPath(doc, "server.ports[1]")).toBe(8002);
    expect(getPath(doc, "bin[0].name")).toBe("one");
  });

  test("returns undefined for a missing path", () => {
    expect(getPath(doc, "server.missing")).toBeUndefined();
    expect(getPath(doc, "server.host.deeper")).toBeUndefined();
  });
});
