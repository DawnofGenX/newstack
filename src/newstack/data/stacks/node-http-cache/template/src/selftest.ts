import { HttpCache, header, maxAgeMs, requestOnce } from "./cache.js";
import { anyMatch, parseList, parseTag, renderTag, strongCompare, strongTag, weakCompare, weakTag } from "./etag.js";
import { library } from "./demo.js";
import { cli, PROGRAM, parse, UsageError } from "./cli.js";
import { Library, representation, cacheControl } from "./resource.js";
import { createServer, respond } from "./server.js";

let passed = 0;
const failures: string[] = [];

function check(name: string, condition: boolean, detail = ""): void {
  if (condition) {
    passed += 1;
    return;
  }
  failures.push(detail === "" ? name : `${name}: ${detail}`);
}

export function report(): number {
  for (const failure of failures) {
    console.error(`  FAIL  ${failure}`);
  }
  console.log(`selftest: ${passed} of ${passed + failures.length} checks passed`);
  return failures.length === 0 ? 0 : 1;
}

async function quietly<T>(work: () => Promise<T>): Promise<{ result: T; output: string }> {
  const lines: string[] = [];
  const log = console.log;
  const error = console.error;
  console.log = (...parts: unknown[]) => {
    lines.push(parts.map(String).join(" "));
  };
  console.error = (...parts: unknown[]) => {
    lines.push(parts.map(String).join(" "));
  };
  try {
    const result = await work();
    return { result, output: lines.join("\n") };
  } finally {
    console.log = log;
    console.error = error;
  }
}

export async function run(): Promise<number> {
  const body = '{"name":"ada"}';
  const strong = strongTag(body);
  const weak = weakTag(body);

  check("a strong tag is quoted", strong.startsWith('"') && strong.endsWith('"'));
  check("a strong tag is not weak", !strong.startsWith("W/"));
  check("a weak tag is marked", weak.startsWith("W/"));
  check("the digest is 16 characters", strong.length === 18, strong);
  check("the same body has the same tag", strongTag(body) === strong);
  check("a different body has a different tag", strongTag(`${body} `) !== strong);

  check("a quoted tag parses", parseTag(strong)?.weak === false);
  check("a weak tag parses as weak", parseTag(weak)?.weak === true);
  check("an unquoted value is not a tag", parseTag("abc") === null);
  check("a truncated tag is not a tag", parseTag('W/"') === null);
  check("rendering round trips", renderTag(parseTag(weak) ?? { weak: false, opaque: "" }) === weak);

  check("weak comparison ignores the marker", weakCompare(parseTag(weak)!, parseTag(strong)!));
  check("strong comparison refuses a weak tag", !strongCompare(parseTag(weak)!, parseTag(strong)!));
  check("strong comparison accepts two strong tags", strongCompare(parseTag(strong)!, parseTag(strong)!));
  check("two weak tags never match strongly", !strongCompare(parseTag(weak)!, parseTag(weak)!));

  check("a list is parsed", parseList(`"a", W/"b"`).tags.length === 2);
  check("a list is not *", !parseList(`"a", W/"b"`).any);
  check("* is recognised", parseList("*").any);
  check("an empty header has nothing", parseList("").tags.length === 0);

  check("weak matching accepts a weak tag", anyMatch(weak, strong, "weak"));
  check("strong matching rejects a weak tag", !anyMatch(weak, strong, "strong"));
  check("a star matches anything", anyMatch("*", strong, "strong"));
  check("an unrelated tag does not match", !anyMatch(strongTag("other"), strong, "weak"));

  const doc = library().get("/profile");
  const varied = library().get("/report");
  const privateDoc = library().get("/private");
  if (doc === undefined || varied === undefined || privateDoc === undefined) {
    throw new Error("fixtures are missing");
  }
  const plain = respond(doc, { method: "GET", accept: "*/*" });
  check("a plain request answers 200", plain.status === 200);
  check("a plain request carries the body", plain.body.length > 0);
  check("a plain request carries a tag", header({ etag: plain.headers["etag"] }, "etag") !== undefined);
  check("a plain request carries a length", plain.headers["content-length"] === String(Buffer.byteLength(plain.body)));

  const notModified = respond(doc, { method: "GET", accept: "*/*", ifNoneMatch: plain.headers["etag"] ?? "" });
  check("a matching tag answers 304", notModified.status === 304);
  check("a 304 has no body", notModified.body === "");
  check("a 304 still carries the tag", notModified.headers["etag"] === plain.headers["etag"]);
  check("a 304 still carries freshness", notModified.headers["cache-control"] === "max-age=60");

  const weakNone = respond(doc, { method: "GET", accept: "*/*", ifNoneMatch: weakTag(plain.body) });
  check("If-None-Match accepts a weak tag", weakNone.status === 304);
  const weakMatch = respond(doc, { method: "PUT", accept: "*/*", ifMatch: weakTag(plain.body) });
  check("If-Match refuses a weak tag", weakMatch.status === 412);
  const strongMatch = respond(doc, { method: "PUT", accept: "*/*", ifMatch: plain.headers["etag"] ?? "" });
  check("If-Match accepts the strong tag", strongMatch.status === 204);
  const unconditionalWrite = respond(doc, { method: "PUT", accept: "*/*" });
  check("a write without If-Match is refused", unconditionalWrite.status === 428);

  const staleDate = "Thu, 01 Jan 1970 00:00:00 GMT";
  const dateOnly = respond(doc, { method: "GET", accept: "*/*", ifModifiedSince: staleDate });
  check("an old date alone answers 200", dateOnly.status === 200);
  const both = respond(doc, {
    method: "GET",
    accept: "*/*",
    ifNoneMatch: plain.headers["etag"] ?? "",
    ifModifiedSince: staleDate,
  });
  check("a matching tag beats an old date", both.status === 304);
  const fresh = respond(doc, { method: "GET", accept: "*/*", ifModifiedSince: new Date(doc.changedAt).toUTCString() });
  check("a current date answers 304", fresh.status === 304);

  const variedJson = respond(varied, { method: "GET", accept: "application/json" });
  const variedText = respond(varied, { method: "GET", accept: "text/plain" });
  check("Vary is announced", variedJson.headers["vary"] === "accept");
  check("the two representations differ", variedJson.body !== variedText.body);
  check("the plain representation is plain", variedText.body.startsWith("/report v1"));
  check("a fixed document does not announce Vary", plain.headers["vary"] === undefined);
  check("representation ignores Accept without Vary", representation(doc, "text/plain") === doc.body);
  check("cache-control counts seconds", cacheControl(doc) === "max-age=60");
  check("no-store is spelled out", cacheControl(privateDoc) === "no-store");
  check("max-age is parsed in ms", maxAgeMs("max-age=1") === 1_000);
  check("no-store has no lifetime", maxAgeMs("no-store") === 0);
  check("a missing header has no lifetime", maxAgeMs(undefined) === 0);

  const keep = new Library([]);
  check("an empty library has no paths", keep.paths().length === 0);
  check("an unknown path is undefined", keep.get("/nope") === undefined);

  const lib = library();
  const handle = await createServer(lib);
  const origin = `http://127.0.0.1:${handle.port}`;
  try {
    let now = 0;
    const cache = new HttpCache(origin, { clock: () => now });
    const first = await cache.get("/ticker");
    check("a cold cache fetches the body", first.bytes > 0 && first.body.length > 0);
    check("a cold cache is not a hit", !first.fromCache);
    const warm = await cache.get("/ticker");
    check("a warm cache answers from memory", warm.fromCache && warm.bytes === 0);
    check("the warm body is the same body", warm.body === first.body);
    now = 1_500;
    const revalidated = await cache.get("/ticker");
    check("an expired entry revalidates", revalidated.revalidated);
    check("a 304 keeps the stored body", revalidated.body === first.body);
    const stored = cache.entry("/ticker", "application/json");
    check("the revalidation is counted", (stored?.revalidations ?? 0) === 1);
    check("the hit is counted", (stored?.hits ?? 0) === 1);

    let bugClock = 0;
    const forgetful = new HttpCache(origin, { clock: () => bugClock, dropBodyOn304: true });
    await forgetful.get("/ticker");
    bugClock = 1_500;
    const lost = await forgetful.get("/ticker");
    check("a cache that copies the 304 body loses it", lost.bodyLost);
    const empty = await forgetful.get("/ticker");
    check("the empty entry is still fresh", empty.fromCache && empty.body === "");

    const urlKeyed = new HttpCache(origin, { clock: () => 0, keyMode: "url" });
    const json = await urlKeyed.get("/report", "application/json");
    const text = await urlKeyed.get("/report", "text/plain");
    check("a url key serves the wrong representation", text.body === json.body);

    const varyKeyed = new HttpCache(origin, { clock: () => 0, keyMode: "vary" });
    const json2 = await varyKeyed.get("/report", "application/json");
    const text2 = await varyKeyed.get("/report", "text/plain");
    check("a vary key serves the right one", text2.body !== json2.body);

    const privateCache = new HttpCache(origin, { clock: () => 0 });
    await privateCache.get("/private");
    check("no-store is not stored", privateCache.entry("/private", "application/json") === undefined);

    const plainFetch = await requestOnce(origin, "/profile", "application/json");
    const conditional = await requestOnce(origin, "/profile", "application/json", {
      "if-none-match": header(plainFetch.headers, "etag") ?? "",
    });
    check("a real 304 has zero bytes", conditional.status === 304 && conditional.bytes === 0);
  } finally {
    await handle.close();
  }

  const version = await quietly(() => cli(["--version"]));
  check("--version exits 0", version.result === 0);
  check("--version names the program", version.output.includes(PROGRAM), version.output);
  const help = await quietly(() => cli(["help"]));
  check("help exits 0", help.result === 0);
  check("help lists the commands", help.output.includes("selftest"));
  const demo = await quietly(() => cli(["demo"]));
  check("demo exits 0", demo.result === 0, String(demo.result));
  check("demo prints six stories", (demo.output.match(/kept        yes/g) ?? []).length === 6);
  const badFlag = await quietly(() => cli(["--rounds", "0"]));
  check("a bad round count exits 2", badFlag.result === 2);
  const unknown = await quietly(() => cli(["nope"]));
  check("an unknown command exits 2", unknown.result === 2);
  const noUrl = await quietly(() => cli(["check"]));
  check("check without a url exits 2", noUrl.result === 2);
  let threw = false;
  try {
    parse(["--port", "0"]);
  } catch (error) {
    threw = error instanceof UsageError;
  }
  check("port 0 is a usage error", threw);

  return report();
}

if (process.argv[1] !== undefined && process.argv[1].endsWith("selftest.js")) {
  const code = await run();
  process.exitCode = code;
}
