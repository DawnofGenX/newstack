import { HttpCache } from "./cache.js";
import { library, render, stories } from "./demo.js";
import { createServer } from "./server.js";
import { run as runSelftest } from "./selftest.js";

export const PROGRAM = "{{ npm_name }}";
export const VERSION = "0.1.0";
export const EXIT_OK = 0;
export const EXIT_BROKEN = 1;
export const EXIT_UNUSABLE = 2;

export class UsageError extends Error {}

export interface Options {
  command: string;
  rounds: number;
  port: number;
  url: string | undefined;
}

export function parse(argv: readonly string[]): Options {
  const [command = "demo", ...rest] = argv;
  const options: Options = { command, rounds: 20, port: 5479, url: undefined };
  for (let index = 0; index < rest.length; index += 1) {
    const flag = rest[index] ?? "";
    const value = rest[index + 1];
    if (flag === "--rounds") {
      if (value === undefined) {
        throw new UsageError("--rounds needs a value");
      }
      const rounds = Number(value);
      if (!Number.isInteger(rounds) || rounds < 1) {
        throw new UsageError(`--rounds must be a positive whole number, not ${value}`);
      }
      options.rounds = rounds;
      index += 1;
    } else if (flag === "--port") {
      if (value === undefined) {
        throw new UsageError("--port needs a value");
      }
      const port = Number(value);
      if (!Number.isInteger(port) || port < 1 || port > 65_535) {
        throw new UsageError(`--port must be between 1 and 65535, not ${value}`);
      }
      options.port = port;
      index += 1;
    } else if (flag === "--url") {
      if (value === undefined) {
        throw new UsageError("--url needs a value");
      }
      options.url = value;
      index += 1;
    } else {
      throw new UsageError(`unknown option ${flag}`);
    }
  }
  return options;
}

export async function check(url: string, rounds: number): Promise<{ kept: boolean; lines: string[] }> {
  const cache = new HttpCache(url);
  let transferred = 0;
  let naive = 0;
  for (let index = 0; index < rounds; index += 1) {
    const outcome = await cache.get("/ticker");
    transferred += outcome.bytes;
    naive += Buffer.byteLength(outcome.body, "utf8");
    await new Promise((done) => setTimeout(done, 5));
  }
  const entry = cache.entry("/ticker", "application/json");
  const lines = [
    `url            ${url}`,
    `rounds         ${rounds}`,
    `transferred    ${transferred} byte(s)`,
    `always 200     ${naive} byte(s)`,
    `hits           ${String(entry?.hits ?? 0)}`,
    `revalidations  ${String(entry?.revalidations ?? 0)}`,
  ];
  const kept = transferred <= naive;
  lines.push(`contract       ${kept ? "kept" : "BROKEN"}`);
  return { kept, lines };
}

export async function cli(argv: readonly string[]): Promise<number> {
  const [first = ""] = argv;
  if (first === "--version" || first === "version") {
    console.log(`${PROGRAM} ${VERSION}`);
    return EXIT_OK;
  }
  if (first === "--help" || first === "help" || first === "") {
    console.log(`usage: ${PROGRAM} <demo|check|serve|selftest> [options]`);
    console.log("  demo                        six stories about conditional requests");
    console.log("  check  --url URL [--rounds N]  measure a cache against a live origin");
    console.log("  serve  [--port N]           serve the demo documents over HTTP");
    console.log("  selftest                    check the rules this stack claims");
    return EXIT_OK;
  }
  let options: Options;
  try {
    options = parse(argv);
  } catch (error) {
    if (error instanceof UsageError) {
      console.error(`${PROGRAM}: ${error.message}`);
      return EXIT_UNUSABLE;
    }
    throw error;
  }
  if (options.command === "demo") {
    const list = await stories();
    console.log(render(list));
    return list.every((story) => story.kept) ? EXIT_OK : EXIT_BROKEN;
  }
  if (options.command === "check") {
    if (options.url === undefined) {
      console.error(`${PROGRAM}: check needs --url`);
      return EXIT_UNUSABLE;
    }
    const result = await check(options.url, options.rounds);
    console.log(result.lines.join("\n"));
    return result.kept ? EXIT_OK : EXIT_BROKEN;
  }
  if (options.command === "serve") {
    const lib = library();
    const handle = await createServer(lib, options.port);
    console.log(`serving ${lib.paths().length} document(s) on http://127.0.0.1:${handle.port}`);
    console.log(`try: curl -i http://127.0.0.1:${handle.port}/profile`);
    await new Promise<void>((resolve) => {
      process.on("SIGINT", () => {
        resolve();
      });
    });
    await handle.close();
    return EXIT_OK;
  }
  if (options.command === "selftest") {
    return runSelftest();
  }
  console.error(`${PROGRAM}: unknown command ${options.command}`);
  return EXIT_UNUSABLE;
}
