// The only module that touches the real process: the filesystem, standard
// input, standard output and standard error.

import type { IO } from "./runner.ts";

function readStdin(): Uint8Array {
  const chunks: Uint8Array[] = [];
  const buffer = new Uint8Array(64 * 1024);
  while (true) {
    const read = Deno.stdin.readSync(buffer);
    if (read === null) break;
    chunks.push(buffer.slice(0, read));
  }
  const length = chunks.reduce((total, chunk) => total + chunk.length, 0);
  const data = new Uint8Array(length);
  let offset = 0;
  for (const chunk of chunks) {
    data.set(chunk, offset);
    offset += chunk.length;
  }
  return data;
}

export function systemIO(): IO {
  const encoder = new TextEncoder();
  return {
    readFile(path: string): Uint8Array | null {
      try {
        return Deno.readFileSync(path);
      } catch {
        return null;
      }
    },
    readStdin,
    out(text: string): void {
      Deno.stdout.writeSync(encoder.encode(text));
    },
    err(text: string): void {
      Deno.stderr.writeSync(encoder.encode(text));
    },
  };
}
