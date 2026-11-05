import { EXIT_BROKEN, EXIT_OK, EXIT_UNUSABLE, PROGRAM, VERSION, run } from "./main.js";
import { Pool, PoolError } from "./pool.js";
import { kib } from "./types.js";

let checks = 0;
let failures = 0;

function check(name: string, held: boolean, detail = ""): void {
  checks += 1;
  if (held) return;
  failures += 1;
  console.log(`FAIL ${name}${detail === "" ? "" : `: ${detail}`}`);
}

function equal(name: string, actual: unknown, wanted: unknown): void {
  check(name, Object.is(actual, wanted), `got ${String(actual)}, wanted ${String(wanted)}`);
}

// console only: stubbing process.stdout would silence the runner as well.
async function quietly<T>(fn: () => Promise<T>): Promise<T> {
  const error = console.error;
  const log = console.log;
  console.error = () => undefined;
  console.log = () => undefined;
  try {
    return await fn();
  } finally {
    console.error = error;
    console.log = log;
  }
}

function refuses(name: string, build: () => unknown, needle: string): void {
  try {
    build();
  } catch (error) {
    const message = (error as Error).message;
    check(name, error instanceof PoolError && message.includes(needle), message);
    return;
  }
  check(name, false, "it did not throw");
}

// -- construction ---------------------------------------------------------------------
refuses("a size of zero is refused", () => new Pool({ size: 0 }), "size must be");
refuses("a fractional size is refused", () => new Pool({ size: 1.5 }), "size must be");
refuses("a negative queue is refused", () => new Pool({ maxQueue: -1 }), "maxQueue must be");

// -- reuse ----------------------------------------------------------------------------
const pool = new Pool({ size: 2, maxQueue: 64 });
const sums = await Promise.all(
  Array.from({ length: 12 }, (_, index) => pool.run<number>("sum", { values: [index, 1] })),
);
equal("every task answers", sums.length, 12);
equal("sums are computed in order", sums[0], 1);
const stats = pool.stats();
check("a pool of two spawns at most two", stats.spawns <= 2, `spawns ${stats.spawns}`);
equal("tasks that ran", stats.completed, 12);
equal("nothing failed", stats.failed, 0);
check("the queue is empty afterwards", stats.queued === 0 && stats.busy === 0);
check("the peak queue was recorded", stats.peakQueue >= 1, `peak ${stats.peakQueue}`);

// -- warm -----------------------------------------------------------------------------
const warm = new Pool({ size: 2 });
await warm.warm();
equal("warm spawns the whole pool", warm.stats().spawns, 2);
equal("warm leaves every worker idle", warm.stats().idle, 2);
await warm.close();

// -- transfer -------------------------------------------------------------------------
const buffer = new ArrayBuffer(64 * 1024);
new Uint8Array(buffer).fill(3);
const back = await pool.run<{ value: number; buffer: ArrayBuffer }>("checksum", { buffer }, [buffer]);
equal("a transferred buffer is detached on the sender", buffer.byteLength, 0);
equal("the worker returns the bytes", back.buffer.byteLength, 64 * 1024);
equal("the checksum sees the original bytes", back.value, (64 * 1024 * 3) % 1_000_003);
equal("kib names its unit", kib(64 * 1024), "64.0 KiB");

// -- bounded queue --------------------------------------------------------------------
const tight = new Pool({ size: 1, maxQueue: 1 });
const outcomes = await Promise.all(
  Array.from({ length: 4 }, () =>
    tight.run("spin", { ms: 40 }).then(
      () => "ran",
      (error: Error) => error.message,
    ),
  ),
);
const ran = outcomes.filter((outcome) => outcome === "ran").length;
check("the bounded queue runs what it accepted", ran >= 1, `ran ${ran}`);
check(
  "a full queue refuses instead of growing",
  outcomes.some((outcome) => outcome.includes("maxQueue limit")),
  outcomes.join(" | "),
);
check("the refusal count survives to close", (await tight.close()).refused >= 1);

// -- failures -------------------------------------------------------------------------
const boom = await pool.run("boom").then(
  () => "resolved",
  (error: Error) => error.message,
);
equal("a throwing task rejects with the worker's message", boom, "the task failed on purpose");
const crash = await pool.run("exit").then(
  () => "resolved",
  (error: Error) => error.message,
);
check("a dying worker rejects with its exit code", crash.includes("exited with code 7"), crash);
const recovered = await pool.run<number>("sum", { values: [5, 6] }).then(
  (value) => value,
  () => Number.NaN,
);
equal("the pool keeps working after a crash", recovered, 11);
check("the crashed worker was replaced", pool.stats().replaced >= 1, `replaced ${pool.stats().replaced}`);
check("the replacement was spawned", pool.stats().spawns > 2, `spawns ${pool.stats().spawns}`);

// -- close ----------------------------------------------------------------------------
const report = await pool.close();
check("close reports the work it finished", report.completed >= 14, `completed ${report.completed}`);
check("close reports the failure", report.failed >= 2, `failed ${report.failed}`);
const afterClose = await pool.run("sum", { values: [1] }).then(
  () => "accepted",
  (error: Error) => error.message,
);
check("a closed pool accepts nothing", afterClose.includes("closing"), afterClose);

// -- cli ------------------------------------------------------------------------------
equal("--version exits 0", await quietly(() => run(["--version"])), EXIT_OK);
equal("--help exits 0", await quietly(() => run(["--help"])), EXIT_OK);
equal("the version is declared", VERSION, "0.1.0");
check("the program has a name", PROGRAM.length > 0);
equal(
  "bench keeps its contract",
  await quietly(() => run(["bench", "--size", "2", "--tasks", "8"])),
  EXIT_OK,
);
equal(
  "bench exits 2 on a zero size",
  await quietly(() => run(["bench", "--size", "0"])),
  EXIT_UNUSABLE,
);
equal(
  "bench exits 2 on a non-integer",
  await quietly(() => run(["bench", "--tasks", "many"])),
  EXIT_UNUSABLE,
);
equal(
  "a missing value exits 2",
  await quietly(() => run(["bench", "--tasks"])),
  EXIT_UNUSABLE,
);
equal("an unknown command exits 2", await quietly(() => run(["nope"])), EXIT_UNUSABLE);
equal("demo exits 0", await quietly(() => run(["demo"])), EXIT_OK);
check("the broken exit code is distinct", EXIT_BROKEN === 1);

console.log(`selftest: ${checks - failures} of ${checks} checks passed`);
if (failures > 0) {
  console.log(`selftest: ${failures} check(s) failed`);
  process.exitCode = 1;
}
