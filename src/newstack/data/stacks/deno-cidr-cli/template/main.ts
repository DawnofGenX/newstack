import { main } from "./src/cli.ts";

/** Entry point: reads stdin/files and exits with the code the CLI returned. */
const code = await main(Deno.args, {
  out: (line) => console.log(line),
  err: (line) => console.error(line),
  readStdin: () => new Response(Deno.stdin.readable).text(),
  readFile: (path) => Deno.readTextFile(path),
});

Deno.exit(code);
