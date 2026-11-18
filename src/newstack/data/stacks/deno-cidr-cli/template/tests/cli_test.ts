import { assertEquals } from "./asserts.ts";

import { main, parseArgs } from "../src/cli.ts";

function harness(input: string, files: Record<string, string> = {}) {
  const out: string[] = [];
  const err: string[] = [];
  const io = {
    out: (line: string) => out.push(line),
    err: (line: string) => err.push(line),
    readStdin: () => Promise.resolve(input),
    readFile: (path: string) => {
      const body = files[path];
      return body === undefined
        ? Promise.reject(new Error("missing"))
        : Promise.resolve(body);
    },
  };
  return { io, out, err };
}

Deno.test("parseArgs collects files, flags and help", () => {
  const options = parseArgs(["--json", "--contains", "10.0.0.1", "a.txt"]);
  assertEquals(options.json, true);
  assertEquals(options.contains, "10.0.0.1");
  assertEquals(options.files, ["a.txt"]);
  assertEquals(parseArgs(["--help"]).status, "help");
  assertEquals(parseArgs(["--nope"]).status, "error");
  assertEquals(parseArgs(["--contains"]).status, "error");
});

Deno.test("table output describes each block", async () => {
  const { io, out } = harness("10.1.2.3/8\n# comment\n\n192.168.0.0/30\n");
  assertEquals(await main([], io), 0);
  assertEquals(out.length, 2);
  assertEquals(out[0].startsWith("10.0.0.0/8 "), true);
  assertEquals(out[1].startsWith("192.168.0.0/30 "), true);
});

Deno.test("--contains filters blocks", async () => {
  const { io, out } = harness("10.0.0.0/8\n192.168.0.0/16\n");
  assertEquals(await main(["--contains", "192.168.4.4"], io), 0);
  assertEquals(out.length, 1);
  assertEquals(out[0].startsWith("192.168.0.0/16 "), true);
});

Deno.test("--json prints an array", async () => {
  const { io, out } = harness("192.168.0.0/30\n");
  assertEquals(await main(["--json"], io), 0);
  const payload = JSON.parse(out.join("\n"));
  assertEquals(payload.length, 1);
  assertEquals(payload[0].prefix, 30);
  assertEquals(payload[0].hosts, 2);
  assertEquals(payload[0].network, 3232235520);
});

Deno.test("a bad block exits 1", async () => {
  const { io, err } = harness("10.0.0.0/33\n");
  assertEquals(await main([], io), 1);
  assertEquals(err[0].startsWith("error: prefix 33"), true);
});

Deno.test("an unreadable file exits 1", async () => {
  const { io, err } = harness("", {});
  assertEquals(await main(["missing.txt"], io), 1);
  assertEquals(err[0], "error: cannot open 'missing.txt'");
});

Deno.test("a file is read when named", async () => {
  const { io, out } = harness("", { "blocks.txt": "172.16.0.0/12\n" });
  assertEquals(await main(["blocks.txt"], io), 0);
  assertEquals(out[0].startsWith("172.16.0.0/12 "), true);
});

Deno.test("usage errors exit 2", async () => {
  const { io, err } = harness("");
  assertEquals(await main(["--bogus"], io), 2);
  assertEquals(err[0], "error: unknown option '--bogus'");
});
