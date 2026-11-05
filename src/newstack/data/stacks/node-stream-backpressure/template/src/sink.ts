import { Writable } from "node:stream";

import type { SinkOptions } from "./types.js";

export interface SinkHandle {
  readonly stream: Writable;
  readonly written: number;
  readonly peakBuffered: number;
  readonly calls: number;
}

/**
 * A writable that consumes one chunk per latency tick.
 *
 * Its `writableLength` is the number of bytes the producer has handed over that the sink has
 * not finished with yet: that is the buffer the producer is paying for.
 */
export function slowSink(options: SinkOptions): SinkHandle {
  let written = 0;
  let peakBuffered = 0;
  let calls = 0;
  const stream = new Writable({
    highWaterMark: options.highWaterMark,
    write(chunk: Buffer, _encoding, callback) {
      calls += 1;
      const size = chunk.byteLength;
      const finish = (): void => {
        written += size;
        callback();
      };
      if (options.latencyMs > 0) {
        setTimeout(finish, options.latencyMs);
      } else {
        setImmediate(finish);
      }
    },
  });
  const probe = (): void => {
    peakBuffered = Math.max(peakBuffered, stream.writableLength);
  };
  stream.on("drain", probe);
  return {
    stream,
    get written() {
      return written;
    },
    get peakBuffered() {
      return peakBuffered;
    },
    get calls() {
      return calls;
    },
  };
}
