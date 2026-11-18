import { randomBytes } from "node:crypto";
import { readFileSync } from "node:fs";
import { timestampToIso, uuidV7, format, parse, isUuid, compare } from "./uuid/format.ts";

const USAGE = `Usage: {{ npm_name }} COMMAND [options]

Generate and inspect UUIDv7 identifiers (RFC 9562): time-ordered, so they sort by
creation time as plain text.

Commands:
  gen [--count N]     print N new v7 uuids (default 1)
  parse UUID          print the fields of one uuid
  sort                read uuids on stdin and print them in ascending order
  validate UUID       exit 0 when the uuid is well formed

Options:
  -n, --count N       how many to generate (1-1000)
  -h, --help          show this help and exit

Exit codes:
  0  success
  1  invalid uuid or unreadable input
  2  usage error
`;

const DEFAULT_COUNT = 1;
const MAX_COUNT = 1000;

export function parseArgs(argv: string[]): { command: string; rest: string[]; count: number } {
  const rest: string[] = [];
  let count = DEFAULT_COUNT;
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "-h" || arg === "--help") return { command: "help", rest: [], count };
    if (arg === "-n" || arg === "--count") {
      const value = argv[++i];
      if (value === undefined) throw new Error(`${arg} needs a value`);
      const parsed = Number(value);
      if (!Number.isInteger(parsed) || parsed < 1 || parsed > MAX_COUNT) {
        throw new Error(`--count must be an integer between 1 and ${MAX_COUNT}`);
      }
      count = parsed;
      continue;
    }
    rest.push(arg);
  }
  const [command, ...args] = rest;
  return { command: command ?? "", rest: args, count };
}

type Io = { out: (text: string) => void; err: (text: string) => void; readStdin: () => string };

export async function main(argv: string[], io: Io = defaultIo()): Promise<number> {
  let parsedArgs: { command: string; rest: string[]; count: number };
  try {
    parsedArgs = parseArgs(argv);
  } catch (error) {
    io.err(`{{ npm_name }}: ${(error as Error).message}\n${USAGE}`);
    return 2;
  }

  const { command, rest, count } = parsedArgs;

  if (command === "help") {
    io.out(USAGE);
    return 0;
  }

  if (command === "gen") {
    if (rest.length > 0) {
      io.err(`{{ npm_name }}: gen takes no arguments, got ${rest.length}\n${USAGE}`);
      return 2;
    }
    for (let i = 0; i < count; i++) {
      const stamp = Date.now();
      io.out(`${format(uuidV7(stamp, new Uint8Array(randomBytes(10))))}\n`);
    }
    return 0;
  }

  if (command === "parse") {
    const text = rest[0];
    if (text === undefined) {
      io.err(`{{ npm_name }}: parse needs a uuid\n${USAGE}`);
      return 2;
    }
    try {
      const uuid = parse(text);
      io.out(`uuid=${uuid.text}\nversion=${uuid.version}\nvariant=rfc4122=${uuid.variant}\n`);
      if (uuid.timestampMs !== null) {
        io.out(`timestamp_ms=${uuid.timestampMs}\ntimestamp_iso=${timestampToIso(uuid.timestampMs)}\n`);
      }
      return 0;
    } catch (error) {
      io.err(`{{ npm_name }}: ${(error as Error).message}\n`);
      return 1;
    }
  }

  if (command === "validate") {
    const text = rest[0];
    if (text === undefined) {
      io.err(`{{ npm_name }}: validate needs a uuid\n${USAGE}`);
      return 2;
    }
    if (isUuid(text)) {
      io.out(`${text.trim().toLowerCase()}\n`);
      return 0;
    }
    io.err(`{{ npm_name }}: not a uuid: ${text}\n`);
    return 1;
  }

  if (command === "sort") {
    const lines = io.readStdin().split("\n").map((line) => line.trim()).filter((line) => line.length > 0);
    const bad = lines.find((line) => !isUuid(line));
    if (bad !== undefined) {
      io.err(`{{ npm_name }}: not a uuid: ${bad}\n`);
      return 1;
    }
    for (const line of [...lines].sort(compare)) io.out(`${line.toLowerCase()}\n`);
    return 0;
  }

  io.err(`{{ npm_name }}: unknown command: ${command || "(none)"}\n${USAGE}`);
  return 2;
}

function defaultIo(): Io {
  return {
    out: (text) => process.stdout.write(text),
    err: (text) => process.stderr.write(text),
    readStdin: () => {
      try {
        return readFileSync(0, "utf8");
      } catch {
        return "";
      }
    },
  };
}
