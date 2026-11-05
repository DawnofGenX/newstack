import { run } from "./pipeline.js";
import type { Mode } from "./pipeline.js";
import { drive, ForgettingTransform, TwiceTransform } from "./transform.js";
import { CHUNK_BYTES, chunkSeries, kib, ratio } from "./types.js";
import type { Measure, SinkOptions } from "./types.js";

const CHUNKS = 256;
const OPTIONS: SinkOptions = { highWaterMark: CHUNK_BYTES, latencyMs: 1 };

function line(measure: Measure): string {
  return [
    `  ${measure.mode.padEnd(10)}`,
    `peak ${kib(measure.peakBuffered).padStart(10)}`,
    `(${ratio(measure.peakBuffered, CHUNK_BYTES).padStart(14)})`,
    `waits ${String(measure.waits).padStart(4)}`,
    `${String(measure.ms).padStart(5)} ms`,
    `delivered ${kib(measure.bytes)}`,
  ].join("  ");
}

async function once(mode: Mode, chunks = CHUNKS): Promise<Measure> {
  return run(mode, chunkSeries(chunks), OPTIONS);
}

export async function stories(): Promise<string[]> {
  const lines: string[] = [];
  const total = kib(CHUNKS * CHUNK_BYTES);

  const ignoring = await once("ignoring");
  const honoring = await once("honoring");
  const awaiting = await once("awaiting");
  const piped = await once("pipeline");

  lines.push(
    `sending ${total} through a sink that takes one chunk per millisecond`,
    `(${CHUNKS} chunks of ${kib(CHUNK_BYTES)}, highWaterMark ${kib(CHUNK_BYTES)})`,
    "",
  );

  lines.push(
    "1. a false return is a request, not an error",
    line(ignoring),
    line(honoring),
    `  the sink ended with the same ${total} both ways, and took the same time:`,
    "  waiting for drain cost nothing, because the sink was the bottleneck either way",
    "  the difference is where the waiting happened: in memory, or in the producer",
    "",
  );

  lines.push(
    "2. awaiting something is not awaiting backpressure",
    line(awaiting),
    `  peak with \`await Promise.resolve()\` per write: ${kib(awaiting.peakBuffered)}`,
    `  peak with \`await once(sink, "drain")\` per refusal: ${kib(honoring.peakBuffered)}`,
    "  a promise that is already kept yields the microtask queue, not the buffer",
    "",
  );

  lines.push(
    "3. pipe() and pipeline() were already right",
    line(piped),
    "  node's own machinery pauses the readable when the writable refuses,",
    "  and destroys both sides when either one errors: no manual drain wiring",
    "",
  );

  const forgetting = await drive(new ForgettingTransform(), [1, 2, 3], 150);
  lines.push(
    "4. a transform that forgets its callback stalls without an error",
    `  after ${forgetting.waitedMs} ms: settled=${forgetting.settled}, error=${forgetting.error}`,
    `  chunks that reached the reader: ${forgetting.output} of 3`,
    "  nothing rejects, nothing ends: the pipeline around it waits forever",
    "  this is the usual shape of \"a node process that hangs\"",
    "",
  );

  const twice = await drive(new TwiceTransform(), [1], 150);
  lines.push(
    "5. calling the callback twice is an error, not a duplicate",
    `  error: ${twice.error}`,
    `  chunks pushed: ${twice.output}, settled=${twice.settled}`,
    "  the stream keeps the first completion and fails the second",
    "",
  );

  return lines;
}

export async function render(): Promise<string> {
  return (await stories()).join("\n");
}

if (process.argv[1] !== undefined && import.meta.url === `file://${process.argv[1]}`) {
  process.stdout.write(`${await render()}\n`);
}
