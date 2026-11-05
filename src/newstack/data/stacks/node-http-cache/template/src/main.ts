import { fileURLToPath } from "node:url";
import { cli } from "./cli.js";

export { EXIT_BROKEN, EXIT_OK, EXIT_UNUSABLE, PROGRAM, VERSION, UsageError, check, cli, parse } from "./cli.js";
export type { Options } from "./cli.js";

if (process.argv[1] !== undefined && fileURLToPath(import.meta.url) === process.argv[1]) {
  const code = await cli(process.argv.slice(2));
  process.exitCode = code;
}
