import { readFileSync, writeFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import { compress, decompress, describe, formatStats, stats } from "./compress.js";

const USAGE = `Usage: {{ npm_name }} <command> [options] [file]

Commands:
  compress [file]    gzip a file (or stdin)
  decompress [file]  gunzip a file (or stdin)
  stats <file>       report sizes for a gzip file or any file

Options:
  -l, --level N      compression level 0..9 (default 6)
  -o, --out PATH     write the result to PATH instead of stdout
  -j, --json         machine readable stats
  -h, --help         show this message
`;

function parse(argv) {
  const options = { level: 6, out: null, json: false, help: false, files: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "-h" || arg === "--help") options.help = true;
    else if (arg === "-j" || arg === "--json") options.json = true;
    else if (arg === "-l" || arg === "--level") {
      const raw = argv[++i];
      if (raw === undefined) throw new UsageError(`${arg} needs a value`);
      const level = Number(raw);
      if (!Number.isInteger(level) || level < 0 || level > 9) {
        throw new UsageError(`--level must be an integer 0..9, got ${raw}`);
      }
      options.level = level;
    } else if (arg === "-o" || arg === "--out") {
      const raw = argv[++i];
      if (raw === undefined) throw new UsageError(`${arg} needs a path`);
      options.out = raw;
    } else if (arg.startsWith("-") && arg !== "-") {
      throw new UsageError(`unknown option ${arg}`);
    } else options.files.push(arg);
  }
  return options;
}

export class UsageError extends Error {}

function readInput(path) {
  if (path === undefined || path === "-") return readFileSync(0);
  return readFileSync(path);
}

function emit(options, payload) {
  if (options.out) writeFileSync(options.out, payload);
  else process.stdout.write(payload);
}

export function main(argv, io = { out: process.stdout, err: process.stderr }) {
  let options;
  try {
    options = parse(argv);
  } catch (error) {
    if (error instanceof UsageError) {
      io.err.write(`{{ npm_name }}: ${error.message}\n`);
      return 2;
    }
    throw error;
  }
  if (options.help || options.files.length === 0) {
    io.out.write(USAGE);
    return options.help ? 0 : 2;
  }

  const [command, ...rest] = options.files;
  try {
    if (command === "compress") {
      const original = readInput(rest[0]);
      const packed = compress(original, { level: options.level });
      emit(options, packed);
      io.err.write(`${formatStats(stats(original.length, packed.length))}\n`);
      return 0;
    }
    if (command === "decompress") {
      const packed = readInput(rest[0]);
      emit(options, decompress(packed));
      return 0;
    }
    if (command === "stats") {
      const target = rest[0];
      if (target === undefined) throw new UsageError("stats needs a file");
      const raw = readInput(target);
      const entry = describe(raw);
      if (!entry.compressed) {
        io.out.write(options.json ? `${JSON.stringify({ format: entry.format, bytes: entry.bytes })}\n` : `${entry.format} bytes=${entry.bytes}\n`);
        return 0;
      }
      const report = stats(decompress(raw).length, raw.length);
      io.out.write(options.json ? `${JSON.stringify({ ...report, format: "gzip" })}\n` : `${formatStats(report)}\n`);
      return 0;
    }
    throw new UsageError(`unknown command ${command}`);
  } catch (error) {
    if (error instanceof UsageError) {
      io.err.write(`{{ npm_name }}: ${error.message}\n`);
      return 2;
    }
    io.err.write(`{{ npm_name }}: ${error.message}\n`);
    return 1;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(main(process.argv.slice(2)));
}
