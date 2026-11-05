import { parentPort, threadId } from "node:worker_threads";

import type { Job, JobResult } from "./types.js";

// The worker is a script, not a class: everything it knows how to do is in `handle`, and
// everything it returns goes back through one postMessage so the pool has one shape to parse.
function handle(job: Job): JobResult | null {
  if (job.kind === "sum") {
    const values = job.values ?? [];
    return { id: job.id, ok: true, value: values.reduce((total, value) => total + value, 0), threadId };
  }
  if (job.kind === "checksum") {
    const buffer = job.buffer;
    if (buffer === undefined) throw new Error("checksum needs a buffer");
    const view = new Uint8Array(buffer);
    let total = 0;
    for (const byte of view) total = (total + byte) % 1_000_003;
    // The buffer is posted BACK with a transfer list, so the worker gives up its copy too:
    // a round trip that moves 1 MiB twice and never duplicates it.
    parentPort?.postMessage({ id: job.id, ok: true, value: total, buffer, threadId }, [buffer]);
    return null;
  }
  if (job.kind === "spin") {
    const until = performance.now() + (job.ms ?? 10);
    let spins = 0;
    while (performance.now() < until) spins += 1;
    return { id: job.id, ok: true, value: spins, threadId };
  }
  if (job.kind === "boom") {
    throw new Error("the task failed on purpose");
  }
  if (job.kind === "exit") {
    process.exit(job.code ?? 7);
  }
  throw new Error(`unknown job kind ${String(job.kind)}`);
}

const port = parentPort;
if (port === null) throw new Error("worker.ts must run as a worker thread");

port.on("message", (job: Job) => {
  let result: JobResult | null;
  try {
    result = handle(job);
  } catch (error) {
    const problem = error as Error;
    result = {
      id: job.id,
      ok: false,
      error: { message: problem.message, stack: problem.stack ?? "", name: problem.name },
      threadId,
    };
  }
  if (result !== null) port.postMessage(result);
});
