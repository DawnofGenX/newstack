import { scorePassword } from "./strength.ts";

export async function main(argv: string[]): Promise<number> {
  if (argv.includes("--help") || argv.includes("-h")) {
    process.stdout.write("usage: pwstrength <password>\n");
    return 0;
  }
  if (argv.length === 0) {
    process.stderr.write("usage: pwstrength <password>\n");
    return 2;
  }
  const pw = argv.join(" ");
  const r = scorePassword(pw);
  process.stdout.write(`${r.score} ${r.label} (entropy~${r.entropy})\n`);
  return 0;
}

if (import.meta.main) {
  process.exit(await main(process.argv.slice(2)));
}