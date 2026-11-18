import { assertEquals } from "./asserts.ts";
import { main, parseArgs, UsageError } from "../src/cli.ts";

function harness(files: Record<string, string>, stdin = "") {
  const out: string[] = [];
  const err: string[] = [];
  return {
    out,
    err,
    io: {
      out: (line: string) => out.push(line),
      err: (line: string) => err.push(line),
      readStdin: () => Promise.resolve(stdin),
      readFile: (path: string) => {
        if (!(path in files)) return Promise.reject(new Error("no such file"));
        return Promise.resolve(files[path]);
      },
    },
  };
}

Deno.test("parseArgs defaults", () => {
  const options = parseArgs(["a", "b"]);
  assertEquals([options.left, options.right, options.context, options.statOnly], ["a", "b", 3, false]);
});

Deno.test("parseArgs accepts -U and --unified=n", () => {
  assertEquals(parseArgs(["-U", "0", "a", "b"]).context, 0);
  assertEquals(parseArgs(["--unified=7", "a", "b"]).context, 7);
});

Deno.test("parseArgs rejects bad context and unknown options", () => {
  let thrown = false;
  try {
    parseArgs(["-U", "x", "a", "b"]);
  } catch (error) {
    thrown = error instanceof UsageError;
  }
  assertEquals(thrown, true);
  let alsoThrown = false;
  try {
    parseArgs(["--bogus", "a", "b"]);
  } catch (error) {
    alsoThrown = error instanceof UsageError;
  }
  assertEquals(alsoThrown, true);
});

Deno.test("main prints a unified diff for differing files", async () => {
  const { io, out } = harness({ "a.txt": "one\ntwo\n", "b.txt": "one\nTWO\n" });
  const code = await main(["-U", "0", "a.txt", "b.txt"], io);
  assertEquals(code, 0);
  assertEquals(out, ["--- a.txt", "+++ b.txt", "@@ -2 +2 @@", "-two", "+TWO"]);
});

Deno.test("main prints nothing for identical files", async () => {
  const { io, out } = harness({ "a.txt": "same\n", "b.txt": "same\n" });
  assertEquals(await main(["a.txt", "b.txt"], io), 0);
  assertEquals(out, []);
});

Deno.test("--exit-code turns a difference into exit 1", async () => {
  const { io } = harness({ "a.txt": "1\n", "b.txt": "2\n" });
  assertEquals(await main(["--exit-code", "a.txt", "b.txt"], io), 1);
  const same = harness({ "a.txt": "1\n", "b.txt": "1\n" });
  assertEquals(await main(["--exit-code", "a.txt", "b.txt"], same.io), 0);
});

Deno.test("--stat reports counts instead of hunks", async () => {
  const { io, out } = harness({ "a.txt": "keep\ndrop\n", "b.txt": "keep\nadd\nmore\n" });
  assertEquals(await main(["--stat", "a.txt", "b.txt"], io), 0);
  assertEquals(out, ["a.txt -> b.txt: 2 insertion(s), 1 deletion(s), 3 change(s)"]);
});

Deno.test("-q keeps stdout empty", async () => {
  const { io, out } = harness({ "a.txt": "1\n", "b.txt": "2\n" });
  assertEquals(await main(["-q", "a.txt", "b.txt"], io), 0);
  assertEquals(out, []);
});

Deno.test("dash reads stdin", async () => {
  const { io, out } = harness({ "b.txt": "x\n" }, "y\n");
  assertEquals(await main(["-U", "0", "-", "b.txt"], io), 0);
  assertEquals(out, ["--- -", "+++ b.txt", "@@ -1 +1 @@", "-y", "+x"]);
});

Deno.test("missing file exits 1 with a message", async () => {
  const { io, err } = harness({});
  assertEquals(await main(["a.txt", "b.txt"], io), 1);
  assertEquals(err[0].startsWith("diff: cannot read a.txt"), true);
});

Deno.test("usage errors exit 2", async () => {
  const { io, err } = harness({});
  assertEquals(await main(["only-one"], io), 2);
  assertEquals(err[0].startsWith("diff: expected two files"), true);
});

Deno.test("--help exits 0", async () => {
  const { io, out } = harness({});
  assertEquals(await main(["--help"], io), 0);
  assertEquals(out.length, 1);
});
