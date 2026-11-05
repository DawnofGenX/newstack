import { Worker } from "node:worker_threads";

import { Pool } from "./pool.js";
import type { PoolStats } from "./types.js";
import { kib } from "./types.js";

const WORKER_URL = new URL("./worker.js", import.meta.url);

function summary(stats: PoolStats): string {
  return [
    `spawns ${stats.spawns}`,
    `completed ${stats.completed}`,
    `failed ${stats.failed}`,
    `replaced ${stats.replaced}`,
    `peak queue ${stats.peakQueue}`,
  ].join(", ");
}

async function oneWorkerPerTask(tasks: number): Promise<number> {
  const started = performance.now();
  for (let index = 0; index < tasks; index += 1) {
    await new Promise<void>((resolve, reject) => {
      const worker = new Worker(WORKER_URL);
      worker.once("message", () => {
        resolve();
        void worker.terminate();
      });
      worker.once("error", reject);
      worker.postMessage({ id: 0, kind: "sum", values: [index] });
    });
  }
  return Math.round(performance.now() - started);
}

export async function stories(): Promise<string[]> {
  const lines: string[] = [];

  // 1. reuse
  const pool = new Pool({ size: 4, maxQueue: 2_048 });
  let started = performance.now();
  await Promise.all(Array.from({ length: 64 }, () => pool.run("sum", { values: [1, 2, 3] })));
  const reused = pool.stats();
  const poolMs = Math.round(performance.now() - started);
  const perTaskMs = await oneWorkerPerTask(8);
  lines.push(
    "1. a pool spawns once, a task-per-worker spawns every time",
    `  64 tasks through 4 workers: ${summary(reused)}, ${poolMs} ms`,
    `  8 tasks with a fresh Worker each: 8 spawns, ${perTaskMs} ms ` +
      `(about ${Math.round(perTaskMs / 8)} ms of startup per task)`,
    "  worker startup is the cost a pool exists to avoid",
    "",
  );

  // 2. the loop stays free
  let ticks = 0;
  const timer = setInterval(() => {
    ticks += 1;
  }, 5);
  started = performance.now();
  await Promise.all([
    pool.run("spin", { ms: 60 }),
    pool.run("spin", { ms: 60 }),
    pool.run("spin", { ms: 60 }),
  ]);
  const wall = Math.round(performance.now() - started);
  clearInterval(timer);
  let blockedTicks = 0;
  const timer2 = setInterval(() => {
    blockedTicks += 1;
  }, 5);
  const until = performance.now() + 180;
  while (performance.now() < until) {
    // deliberately block: this is the shape of doing the work on the main thread
  }
  clearInterval(timer2);
  lines.push(
    "2. cpu work in a worker leaves the event loop alone",
    `  3 x 60 ms in workers: ${ticks} timer ticks in ${wall} ms of wall time`,
    `  the same 180 ms on the main thread: ${blockedTicks} ticks`,
    "  an async function does not move work off the loop; a worker does",
    "",
  );

  // 3. transfer
  const buffer = new ArrayBuffer(1024 * 1024);
  new Uint8Array(buffer).fill(7);
  const before = buffer.byteLength;
  const back = await pool.run<{ value: number; buffer: ArrayBuffer }>("checksum", { buffer }, [buffer]);
  lines.push(
    "3. a transferred buffer is moved, not copied",
    `  before the task: ${kib(before)}; after it: ${kib(buffer.byteLength)} on the sender`,
    `  the worker gave it back: ${kib(back.buffer.byteLength)}, checksum ${back.value}`,
    "  a detached buffer is the proof: a copy would have left the sender's bytes intact",
    "",
  );

  // 4. bounded queue
  const tight = new Pool({ size: 1, maxQueue: 2 });
  const outcomes = await Promise.all(
    Array.from({ length: 6 }, () =>
      tight.run("spin", { ms: 30 }).then(
        () => "ran",
        (error: Error) => `refused: ${error.message}`,
      ),
    ),
  );
  const ran = outcomes.filter((outcome) => outcome === "ran").length;
  const refused = outcomes.length - ran;
  lines.push(
    "4. a full queue refuses instead of growing",
    `  size 1, maxQueue 2, six tasks in one tick: ${ran} ran, ${refused} refused`,
    `  the refusal: ${outcomes.find((outcome) => outcome.startsWith("refused")) ?? "none"}`,
    "  a queue with no bound is a memory leak with extra steps",
    "",
  );
  await tight.close();

  // 5. crashes
  const boom = await pool.run("boom").then(
    () => "resolved",
    (error: Error) => error.message,
  );
  const crash = await pool.run("exit").then(
    () => "resolved",
    (error: Error) => error.message,
  );
  const afterCrash = await pool.run<number>("sum", { values: [5, 6] }).then(
    (value) => `ok ${String(value)}`,
    (error: Error) => `failed ${error.message}`,
  );
  const healthy = pool.stats();
  lines.push(
    "5. a crashed worker is not a finished task",
    `  a throwing task: ${boom}`,
    `  a task that calls process.exit(7): ${crash}`,
    `  the next task: ${afterCrash}; the pool replaced the worker (spawns ${healthy.spawns}, ` +
      `replaced ${healthy.replaced})`,
    "  a worker that dies without answering must reject, never hang",
    "",
  );

  // 6. close
  const done = await Promise.all([pool.run("sum", { values: [2] }), pool.run("sum", { values: [3] })]);
  const report = await pool.close();
  lines.push(
    "6. close drains the backlog before the threads go",
    `  pending results: ${done.join(", ")}`,
    `  close report: ${JSON.stringify(report)}`,
    "  there is no task that was accepted and then silently dropped",
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
