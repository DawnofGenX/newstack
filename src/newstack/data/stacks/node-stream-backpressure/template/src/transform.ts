import { Transform } from "node:stream";
import type { TransformCallback } from "node:stream";

/**
 * A transform that pushes its input through but forgets to call the callback.
 *
 * Nothing errors, nothing ends: the stream is simply waiting, forever, and a `pipeline()`
 * around it never settles. This is the most common way a Node stream "hangs".
 */
export class ForgettingTransform extends Transform {
  constructor() {
    super({ objectMode: true });
  }

  override _transform(chunk: unknown, _encoding: BufferEncoding, _callback: TransformCallback): void {
    this.push(chunk);
  }
}

/** A transform that calls its callback twice: the second call is an error, not a no-op. */
export class TwiceTransform extends Transform {
  constructor() {
    super({ objectMode: true });
    this.on("error", () => undefined);
  }

  override _transform(chunk: unknown, _encoding: BufferEncoding, callback: TransformCallback): void {
    callback(null, chunk);
    callback(null, chunk);
  }
}

export interface StallReport {
  readonly settled: boolean;
  readonly error: string | null;
  readonly output: number;
  readonly waitedMs: number;
}

/**
 * Drive a transform and wait a bounded time.
 *
 * A stream that is not finished after `waitedMs` and has not errored is stalled: `settled`
 * stays false, and that false is the diagnosis.
 */
export async function drive(
  transform: Transform,
  chunks: readonly unknown[],
  waitedMs: number,
): Promise<StallReport> {
  let output = 0;
  let error: string | null = null;
  let settled = false;
  transform.on("data", () => {
    output += 1;
  });
  transform.on("error", (problem: Error) => {
    error = problem.message;
  });
  transform.on("finish", () => {
    settled = true;
  });
  for (const chunk of chunks) {
    transform.write(chunk);
  }
  transform.end();
  await new Promise((resolve) => {
    const timer = setTimeout(resolve, waitedMs);
    transform.on("close", () => {
      clearTimeout(timer);
      resolve(undefined);
    });
  });
  return { settled, error, output, waitedMs };
}
