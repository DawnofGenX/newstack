/** Offline checks: the whole contract without opening a socket. */
import { countText } from "./counts.js";
import { jsonQuote, percentDecode, queryText, readTextMember, route, statsBody } from "./contract.js";

interface Tally {
  checks: number;
  failures: number;
}

function check(tally: Tally, name: string, ok: boolean): void {
  tally.checks += 1;
  if (ok) {
    process.stdout.write(`ok ${name}\n`);
  } else {
    tally.failures += 1;
    process.stdout.write(`FAIL ${name}\n`);
  }
}

export function runSelftest(): number {
  const tally: Tally = { checks: 0, failures: 0 };

  check(tally, "count empty", JSON.stringify(countText("")) === '{"lines":0,"words":0,"bytes":0}');
  check(tally, "count one line", countText("a b\n").lines === 1);
  check(tally, "count words", countText("a b\n").words === 2);
  check(tally, "count bytes", countText("a b\n").bytes === 4);
  check(tally, "two lines", countText("a b\nc\n").lines === 2);
  check(tally, "two-line words", countText("a b\nc\n").words === 3);
  check(tally, "accents are bytes", countText("héllo wörld\n").bytes === 14);
  check(tally, "accents are not words", countText("héllo wörld\n").words === 2);
  check(tally, "no trailing newline", countText("a b\nc").lines === 1);
  check(tally, "vertical tab separates", countText("a\u000bb").words === 2);
  check(tally, "form feed separates", countText("a\u000cb").words === 2);
  check(tally, "carriage return separates", countText("a\rb").words === 2);

  check(tally, "percent space", percentDecode("a+b") === "a b");
  check(tally, "percent accent", percentDecode("caf%C3%A9") === "café");
  check(tally, "percent plus literal", percentDecode("a%2Bb") === "a+b");
  check(tally, "percent broken escape", percentDecode("100%") === "100%");
  check(tally, "query first wins", queryText("/stats?text=one&text=two") === "one");
  check(tally, "query missing", queryText("/stats") === undefined);
  check(tally, "query empty value", queryText("/stats?text=") === "");
  check(tally, "query other key", queryText("/stats?other=x") === undefined);

  check(tally, "quote plain", jsonQuote("a") === '"a"');
  check(tally, "quote newline", jsonQuote("a\nb") === '"a\\nb"');
  check(tally, "quote quote", jsonQuote('a"b') === '"a\\"b"');
  check(tally, "quote accent kept", jsonQuote("café") === '"café"');

  const body = statsBody("a b\n");
  check(tally, "stats key order", Object.keys(body).join(",") === "text,lines,words,bytes");
  check(tally, "stats numbers", body.lines === 1 && body.words === 2 && body.bytes === 4);

  const health = route({ method: "GET", target: "/health", body: undefined });
  check(tally, "health 200", health.status === 200);
  check(tally, "health body", JSON.stringify(health.body) === '{"status":"ok"}');
  const healthPost = route({ method: "POST", target: "/health", body: "" });
  check(tally, "health 405", healthPost.status === 405);

  const getStats = route({ method: "GET", target: "/stats?text=caf%C3%A9", body: undefined });
  check(tally, "get decodes", getStats.status === 200 && (getStats.body as { text: string }).text === "café");
  const getEmpty = route({ method: "GET", target: "/stats", body: undefined });
  check(tally, "get without text counts empty", (getEmpty.body as { bytes: number }).bytes === 0);

  const post = route({ method: "POST", target: "/stats", body: '{"text":"a b\\nc\\n"}' });
  check(tally, "post ok", post.status === 200);
  check(tally, "post counts", JSON.stringify(post.body) === '{"text":"a b\\nc\\n","lines":2,"words":3,"bytes":6}');
  check(tally, "post missing", route({ method: "POST", target: "/stats", body: "{}" }).status === 422);
  check(
    tally,
    "post missing error",
    JSON.stringify(route({ method: "POST", target: "/stats", body: "{}" }).body) === '{"error":"missing_text"}',
  );
  check(tally, "post number", route({ method: "POST", target: "/stats", body: '{"text":42}' }).status === 422);
  check(tally, "post broken", route({ method: "POST", target: "/stats", body: '{"text":' }).status === 422);
  check(tally, "post array", route({ method: "POST", target: "/stats", body: "[1]" }).status === 422);
  check(tally, "put stats 405", route({ method: "PUT", target: "/stats", body: "" }).status === 405);
  check(tally, "unknown path", route({ method: "GET", target: "/nope?x=1", body: undefined }).status === 404);
  check(
    tally,
    "unknown detail",
    JSON.stringify(route({ method: "GET", target: "/nope?x=1", body: undefined }).body) ===
      '{"error":"not_found","detail":"no route for GET /nope"}',
  );
  check(tally, "read text", JSON.stringify(readTextMember('{"text":"x"}')) === '{"kind":"text","text":"x"}');
  check(tally, "read missing", readTextMember("{}").kind === "missing");
  check(tally, "read invalid", readTextMember("{").kind === "invalid");

  const failed = tally.failures;
  process.stdout.write(`checks: ${tally.checks}, passed: ${tally.checks - failed}, failed: ${failed}\n`);
  return failed === 0 ? 0 : 1;
}
