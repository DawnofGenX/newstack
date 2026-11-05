import { EXIT_OK, EXIT_STALLED, EXIT_UNUSABLE, PROGRAM, run, VERSION } from "./main.js";
import { run as measureRun } from "./pipeline.js";
import { slowSink } from "./sink.js";
import { ForgettingTransform, TwiceTransform, drive } from "./transform.js";
import { CHUNK_BYTES, chunkSeries, kib, ratio } from "./types.js";

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

// Only console is stubbed: patching process.stdout.write would also silence the
// test runner's own reporter, which writes there asynchronously.
async function quietAsync<T>(fn: () => Promise<T>): Promise<T> {
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

const CHUNKS = 64;
const OPTIONS = { highWaterMark: CHUNK_BYTES, latencyMs: 1 };
const series = chunkSeries(CHUNKS);
const totalBytes = CHUNKS * CHUNK_BYTES;

// -- the pieces -----------------------------------------------------------------------
const small = chunkSeries(3, 1024);
equal("chunkSeries keeps the count", small.length, 3);
equal("chunkSeries keeps the size", small[0]?.byteLength, 1024);
equal("kib prints one decimal", kib(16 * 1024), "16.0 KiB");
equal("kib of nothing", kib(0), "0.0 KiB");
equal("ratio names the unit", ratio(2 * CHUNK_BYTES, CHUNK_BYTES), "2.0x a chunk");

const sink = slowSink({ highWaterMark: CHUNK_BYTES, latencyMs: 0 });
const accepted = sink.stream.write(new Uint8Array(CHUNK_BYTES));
check("a sink with a full highWaterMark refuses one more chunk", !accepted);
sink.stream.destroy();

// -- the four producers ---------------------------------------------------------------
const ignoring = await measureRun("ignoring", series, OPTIONS);
const awaiting = await measureRun("awaiting", series, OPTIONS);
const honoring = await measureRun("honoring", series, OPTIONS);
const piped = await measureRun("pipeline", series, OPTIONS);

for (const measure of [ignoring, awaiting, honoring, piped]) {
  equal(`${measure.mode} delivers every byte`, measure.bytes, totalBytes);
}
equal("ignoring counts its chunks", ignoring.chunks, CHUNKS);
equal("ignoring never waits", ignoring.waits, 0);
check(
  "ignoring buffers the whole series",
  ignoring.peakBuffered > 20 * CHUNK_BYTES,
  `peak ${kib(ignoring.peakBuffered)}`,
);
check(
  "awaiting a kept promise is not backpressure",
  awaiting.peakBuffered > 20 * CHUNK_BYTES,
  `peak ${kib(awaiting.peakBuffered)}`,
);
check(
  "honoring keeps the buffer near one chunk",
  honoring.peakBuffered <= 2 * CHUNK_BYTES,
  `peak ${kib(honoring.peakBuffered)} (${ratio(honoring.peakBuffered, CHUNK_BYTES)})`,
);
check("honoring waits when the sink refuses", honoring.waits >= 1, `waits ${honoring.waits}`);
check(
  "pipeline keeps the buffer near one chunk",
  piped.peakBuffered <= 2 * CHUNK_BYTES,
  `peak ${kib(piped.peakBuffered)}`,
);
equal("honoring reports no stalls", honoring.stalls, 0);
check(
  "honoring is not slower than ignoring by more than noise",
  honoring.ms <= ignoring.ms + 250,
  `honoring ${honoring.ms} ms, ignoring ${ignoring.ms} ms`,
);

// -- the two transform mistakes -------------------------------------------------------
const forgetting = await drive(new ForgettingTransform(), [1, 2, 3], 100);
check("a forgotten callback never settles", !forgetting.settled);
equal("a forgotten callback raises no error", forgetting.error, null);
check("a forgotten callback still passes the first chunk", forgetting.output >= 1);

const twice = await drive(new TwiceTransform(), [1], 100);
check(
  "a doubled callback is an error",
  twice.error !== null && twice.error.includes("multiple times"),
  String(twice.error),
);
check("a doubled callback never settles", !twice.settled);

// -- the cli --------------------------------------------------------------------------
equal("--version exits 0", await quietAsync(() => run(["--version"])), EXIT_OK);
equal("--help exits 0", await quietAsync(() => run(["--help"])), EXIT_OK);
equal("dev version banner matches the module", VERSION, "0.1.0");
equal(
  "compare exits 0 when the bounded mode holds",
  await quietAsync(() => run(["compare", "--chunks", "24", "--latency", "1"])),
  EXIT_OK,
);
equal(
  "compare exits 1 when the bound is impossible",
  await quietAsync(() =>
    run(["compare", "--chunks", "24", "--latency", "1", "--max-peak-chunks", "0"]),
  ),
  EXIT_STALLED,
);
equal(
  "compare exits 2 on zero chunks",
  await quietAsync(() => run(["compare", "--chunks", "0"])),
  EXIT_UNUSABLE,
);
equal(
  "compare exits 2 on a non-integer",
  await quietAsync(() => run(["compare", "--chunks", "many"])),
  EXIT_UNUSABLE,
);
equal(
  "compare exits 2 on a missing value",
  await quietAsync(() => run(["compare", "--chunks"])),
  EXIT_UNUSABLE,
);
equal("an unknown command is unusable", await quietAsync(() => run(["nope"])), EXIT_UNUSABLE);
equal("demo exits 0", await quietAsync(() => run(["demo"])), EXIT_OK);

console.log(`selftest: ${checks - failures} of ${checks} checks passed`);
if (failures > 0) {
  console.log(`selftest: ${failures} check(s) failed`);
  process.exitCode = 1;
}
