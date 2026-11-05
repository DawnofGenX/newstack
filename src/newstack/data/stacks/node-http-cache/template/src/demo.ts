import { HttpCache, header, maxAgeMs, requestOnce } from "./cache.js";
import { strongTag, weakTag } from "./etag.js";
import { Library, document } from "./resource.js";
import { createServer, respond } from "./server.js";

export interface Story {
  title: string;
  lines: string[];
  kept: boolean;
}

export function library(): Library {
  return new Library([
    document("/profile", { name: "ada", role: "engineer", team: "core" }, { maxAgeMs: 60_000 }),
    document("/report", { total: 3, note: "json for machines" }, { maxAgeMs: 60_000, varyAccept: true }),
    document("/ticker", { price: 42 }, { maxAgeMs: 1_000 }),
    document("/private", { secret: "do not store" }, { maxAgeMs: 0 }),
  ]);
}

function bytes(text: string): number {
  return Buffer.byteLength(text, "utf8");
}

function oneLine(text: string): string {
  return text.replace(/\s+/g, " ").trim().slice(0, 34);
}

export async function stories(): Promise<Story[]> {
  const out: Story[] = [];
  const lib = library();
  const handle = await createServer(lib);
  const origin = `http://127.0.0.1:${handle.port}`;
  try {
    const profile = lib.get("/profile");
    if (profile === undefined) {
      throw new Error("fixture /profile is missing");
    }

    // 1
    const plain = await requestOnce(origin, "/profile", "application/json");
    const tag = header(plain.headers, "etag") ?? "";
    const conditional = await requestOnce(origin, "/profile", "application/json", {
      "if-none-match": tag,
    });
    out.push({
      title: "1. a 304 carries no body",
      lines: [
        `first request   ${plain.status}, ${plain.bytes} byte(s), ${tag}`,
        `conditional     ${conditional.status}, ${conditional.bytes} byte(s) of body`,
        `the tag is the same document, so the body was not sent twice`,
        `saved           ${plain.bytes} byte(s)`,
      ],
      kept: conditional.status === 304 && conditional.bytes === 0 && plain.bytes > 0,
    });

    // 2
    const weak = weakTag(profile.body);
    const strong = strongTag(profile.body);
    const weakNone = respond(profile, { method: "GET", accept: "*/*", ifNoneMatch: weak });
    const weakMatch = respond(profile, { method: "PUT", accept: "*/*", ifMatch: weak });
    const strongMatch = respond(profile, { method: "PUT", accept: "*/*", ifMatch: strong });
    out.push({
      title: "2. If-None-Match compares weakly, If-Match strongly",
      lines: [
        `If-None-Match: ${weak}   -> ${weakNone.status} (weak comparison ignores W/)`,
        `If-Match:      ${weak}   -> ${weakMatch.status} (strong comparison only)`,
        `If-Match:      ${strong} -> ${strongMatch.status}`,
        `so a weak tag can say "unchanged" but can never authorise a write`,
      ],
      kept: weakNone.status === 304 && weakMatch.status === 412 && strongMatch.status === 204,
    });

    // 3
    const both = respond(profile, {
      method: "GET",
      accept: "*/*",
      ifNoneMatch: strong,
      ifModifiedSince: "Thu, 01 Jan 1970 00:00:00 GMT",
    });
    const dateOnly = respond(profile, {
      method: "GET",
      accept: "*/*",
      ifModifiedSince: "Thu, 01 Jan 1970 00:00:00 GMT",
    });
    out.push({
      title: "3. If-None-Match wins over If-Modified-Since",
      lines: [
        `date alone                    -> ${dateOnly.status} (the stored copy looks old)`,
        `date and a matching tag       -> ${both.status} (the tag is more precise)`,
        `a cache that reads the date first refetches a body it already has`,
      ],
      kept: dateOnly.status === 200 && both.status === 304,
    });

    // 4
    let now = 0;
    const urlKeyed = new HttpCache(origin, { clock: () => now, keyMode: "url" });
    const varyKeyed = new HttpCache(origin, { clock: () => now, keyMode: "vary" });
    const asJson = await urlKeyed.get("/report", "application/json");
    const asTextFromUrlKey = await urlKeyed.get("/report", "text/plain");
    const asJsonVary = await varyKeyed.get("/report", "application/json");
    const asTextVary = await varyKeyed.get("/report", "text/plain");
    out.push({
      title: "4. Vary: accept means the URL alone is not a key",
      lines: [
        `json keyed by url   ${oneLine(asJson.body)}`,
        `text keyed by url   ${oneLine(asTextFromUrlKey.body)}   <- wrong representation`,
        `json keyed by vary  ${oneLine(asJsonVary.body)}`,
        `text keyed by vary  ${oneLine(asTextVary.body)}`,
      ],
      kept:
        !asTextFromUrlKey.body.includes("v1") &&
        asTextVary.body.includes("v1") &&
        asTextVary.body !== asJsonVary.body,
    });

    // 5
    let clock = 0;
    let bugClock = 0;
    const careful = new HttpCache(origin, { clock: () => clock });
    const forgetful = new HttpCache(origin, { clock: () => bugClock, dropBodyOn304: true });
    const first = await careful.get("/ticker");
    clock = 1_500;
    const refreshed = await careful.get("/ticker");
    const afterRefresh = await careful.get("/ticker");
    const bugFirst = await forgetful.get("/ticker");
    bugClock = 1_500;
    const bugRefresh = await forgetful.get("/ticker");
    const bugAfter = await forgetful.get("/ticker");
    out.push({
      title: "5. a 304 refreshes freshness, it does not empty the body",
      lines: [
        `stored          ${bytes(first.body)} byte(s)`,
        `after a 304     ${bytes(refreshed.body)} byte(s), revalidated ${String(refreshed.revalidated)}`,
        `next hit        ${bytes(afterRefresh.body)} byte(s)`,
        `drop-on-304     ${bytes(bugFirst.body)} -> ${bytes(bugRefresh.body)} byte(s), lost ${String(bugRefresh.bodyLost)}`,
        `its next hit    ${bytes(bugAfter.body)} byte(s): the entry is now empty and still fresh`,
      ],
      kept:
        bytes(refreshed.body) > 0 &&
        bytes(afterRefresh.body) > 0 &&
        bugRefresh.bodyLost &&
        bytes(bugAfter.body) === 0,
    });

    // 6
    let rounds = 0;
    let ticker = 0;
    const measured = new HttpCache(origin, { clock: () => ticker });
    const entry = () => measured.entry("/ticker", "application/json");
    for (let index = 0; index < 20; index += 1) {
      ticker = index * 300;
      const outcome = await measured.get("/ticker");
      rounds += outcome.bytes;
    }
    const stored = entry();
    const naive = bytes((await requestOnce(origin, "/ticker", "application/json")).body) * 20;
    out.push({
      title: "6. the saved bytes are counted, not estimated",
      lines: [
        `20 rounds       ${rounds} byte(s) over the wire`,
        `always 200      ${naive} byte(s)`,
        `hits            ${String(stored?.hits ?? 0)}`,
        `revalidations   ${String(stored?.revalidations ?? 0)}`,
        `saved           ${naive - rounds} byte(s) (${(((naive - rounds) / naive) * 100).toFixed(1)}%)`,
        `ttl parsed      ${maxAgeMs("max-age=1")} ms from max-age=1`,
      ],
      kept: rounds < naive && (stored?.revalidations ?? 0) > 0 && (stored?.hits ?? 0) > 0,
    });
  } finally {
    await handle.close();
  }
  return out;
}

export function render(list: readonly Story[]): string {
  const parts: string[] = [];
  for (const story of list) {
    parts.push(story.title);
    for (const line of story.lines) {
      parts.push(`  ${line}`);
    }
    parts.push(`  kept        ${story.kept ? "yes" : "NO"}`);
    parts.push("");
  }
  return parts.join("\n");
}
