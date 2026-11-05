import { once } from "node:events";
import { Readable } from "node:stream";
import { finished, pipeline } from "node:stream/promises";

import { slowSink } from "./sink.js";
import type { Measure, SinkOptions } from "./types.js";

export type Mode = "ignoring" | "awaiting" | "honoring" | "pipeline";

/**
 * Run the same chunk series through the same slow sink in one of four ways.
 *
 * The sink is identical every time, so any difference in `peakBuffered` is the producer's
 * doing: ignoring a false return, awaiting something that is not backpressure, or waiting for
 * the real `drain`.
 */
export async function run(
  mode: Mode,
  chunks: readonly Uint8Array[],
  options: SinkOptions,
): Promise<Measure> {
  const sink = slowSink(options);
  let peak = 0;
  let waits = 0;
  let bytes = 0;
  const started = performance.now();
  const sample = (): void => {
    peak = Math.max(peak, sink.stream.writableLength);
  };

  if (mode === "pipeline") {
    const ticker = setInterval(sample, 1);
    ticker.unref();
    try {
      await pipeline(Readable.from(chunks), sink.stream);
    } finally {
      clearInterval(ticker);
    }
    bytes = sink.written;
  } else {
    for (const chunk of chunks) {
      const accepted = sink.stream.write(chunk);
      sample();
      if (mode === "ignoring") {
        continue;
      }
      if (mode === "awaiting") {
        await Promise.resolve();
        sample();
        continue;
      }
      if (!accepted) {
        waits += 1;
        await once(sink.stream, "drain");
        sample();
      }
    }
    sink.stream.end();
    await finished(sink.stream);
    bytes = sink.written;
  }

  return {
    mode,
    chunks: chunks.length,
    bytes,
    peakBuffered: peak,
    waits,
    stalls: 0,
    ms: Math.round(performance.now() - started),
  };
}
