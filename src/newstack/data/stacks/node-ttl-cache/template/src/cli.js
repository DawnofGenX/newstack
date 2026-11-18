#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { createCache } from "./cache.js";

const PROGRAM = "{{ npm_name }}";
const USAGE = `usage: ${PROGRAM} [--capacity N] [--ttl MS] [FILE]

Reads commands from FILE (or stdin) one per line and keeps a TTL cache:
  SET key value [ttlMs]   store value (JSON or a bare word) for ttlMs
  GET key                 print the value, or (nil)
  DEL key                 print 1 when the key existed, else 0
  KEYS                    print the keys, least recently used first
  SWEEP                   print how many expired entries were dropped
  ADVANCE ms              move the virtual clock forward
  STATS                   print the counters
  QUIT                    stop reading`;

function parseValue(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
}

export function run(lines, { capacity, ttlMs, out = (line) => console.log(line) }) {
  let clock = 0;
  const cache = createCache({ capacity, ttlMs, now: () => clock });
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed === "" || trimmed.startsWith("#")) continue;
    const [command, ...args] = trimmed.split(/\s+/);
    switch (command.toUpperCase()) {
      case "SET": {
        if (args.length < 2) return { code: 1, error: "SET needs a key and a value" };
        const [key, raw, ttl] = args;
        const options = ttl === undefined ? {} : { ttlMs: Number(ttl) };
        if (options.ttlMs !== undefined && !Number.isFinite(options.ttlMs)) {
          return { code: 1, error: `SET ttl must be a number, got ${ttl}` };
        }
        cache.set(key, parseValue(raw), options);
        out("OK");
        break;
      }
      case "GET": {
        if (args.length !== 1) return { code: 1, error: "GET needs exactly one key" };
        const value = cache.get(args[0]);
        out(value === undefined ? "(nil)" : JSON.stringify(value));
        break;
      }
      case "DEL": {
        if (args.length !== 1) return { code: 1, error: "DEL needs exactly one key" };
        out(cache.delete(args[0]) ? "1" : "0");
        break;
      }
      case "KEYS":
        out(cache.keys().join(" "));
        break;
      case "SWEEP":
        out(`swept=${cache.sweep()}`);
        break;
      case "ADVANCE": {
        const step = Number(args[0]);
        if (!Number.isFinite(step) || step < 0) {
          return { code: 1, error: `ADVANCE needs a non-negative number, got ${args[0]}` };
        }
        clock += step;
        out(`now=${clock}`);
        break;
      }
      case "STATS": {
        const stats = cache.stats();
        out(
          `hits=${stats.hits} misses=${stats.misses} evictions=${stats.evictions} ` +
            `expirations=${stats.expirations} entries=${stats.entries}`,
        );
        break;
      }
      case "QUIT":
        return { code: 0 };
      default:
        return { code: 1, error: `unknown command: ${command}` };
    }
  }
  return { code: 0 };
}

export function main(argv, io = {}) {
  const out = io.out ?? ((line) => console.log(line));
  const err = io.err ?? ((line) => console.error(line));
  let capacity = 128;
  let ttlMs = 0;
  const positional = [];
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "-h" || arg === "--help") {
      out(USAGE);
      return 0;
    }
    if (arg === "--capacity" || arg === "--ttl") {
      const value = Number(argv[index + 1]);
      if (!Number.isFinite(value)) {
        err(`${arg} needs a number`);
        return 2;
      }
      if (arg === "--capacity") capacity = value;
      else ttlMs = value;
      index += 1;
    } else if (arg.startsWith("-")) {
      err(`unknown option: ${arg}`);
      err(USAGE);
      return 2;
    } else {
      positional.push(arg);
    }
  }
  let text;
  try {
    text = positional.length === 0 ? readFileSync(0, "utf8") : readFileSync(positional[0], "utf8");
  } catch (error) {
    err(`cannot read ${positional[0] ?? "stdin"}: ${error.message}`);
    return 1;
  }
  const result = run(text.split(/\r?\n/), { capacity, ttlMs, out });
  if (result.error) err(result.error);
  return result.code;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv.slice(2)));
}
