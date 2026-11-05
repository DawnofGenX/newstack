# {{ title }}

{{ description }}

A sink accepts a chunk per millisecond. Every producer below writes the same series of chunks
into the same sink. The only thing that changes is what the producer does when `write()` returns
`false`, and the only number that matters is `writableLength`: the bytes the producer has handed
over that the sink has not finished with yet.

```
{{ npm_name }} compare --chunks 256 --latency 1
256 chunks of 16.0 KiB through a sink taking one per 1 ms
  ignoring    peak 4096.0 KiB  (256.0x a chunk)  waits    0     272 ms  delivered 4096.0 KiB
  awaiting    peak 4096.0 KiB  (256.0x a chunk)  waits    0     266 ms  delivered 4096.0 KiB
  honoring    peak   16.0 KiB  (  1.0x a chunk)  waits  256     268 ms  delivered 4096.0 KiB
bounded    yes: peak 16.0 KiB against a limit of 32.0 KiB
```

## The rules this stack keeps

1. **A `false` return is a request, not an error.** Nothing throws, nothing is lost, and the
   write still lands. It means "I am at my highWaterMark; stop handing me more until `drain`".
   Ignoring it is legal and it is how a 4 MiB series becomes 4 MiB of resident memory.
2. **`await Promise.resolve()` is not backpressure.** It yields the microtask queue, which is
   already empty by the time the next chunk is written. The table above shows it: the peak is
   identical to ignoring, because it is ignoring with extra steps.
3. **Only `drain` is backpressure.** `once(stream, "drain")` resolves when the sink has fallen
   below its highWaterMark. In the table it costs 2 ms of wall time, because the sink was the
   bottleneck either way; the difference is whether the queue lives in the stream or in your
   process.
4. **`pipeline()` already does this.** Node pauses the readable when the writable refuses and
   destroys both sides on error. Hand-wiring `drain` is only needed when you own the loop.
5. **A transform that forgets its callback does not error.** It pushes, then waits forever.
   `settled` stays `false` with no error, no `finish`, no rejection: the usual shape of "my Node
   process hangs".
6. **Calling a transform callback twice is an error, not a duplicate.** The stream fails with
   `Callback called multiple times` and keeps the first completion.
7. **The peak is sampled, not guessed.** `writableLength` is read after every write and after
   every `drain`, so the reported number is a real high-water mark of the real buffer.

## What the demo shows

```
node dist/src/main.js demo
```

Five stories, all from live runs rather than constants:

- a false return is a request, not an error — the same bytes and the same wall time, with the
  peak moving between the stream and the process;
- awaiting something is not awaiting backpressure — `await Promise.resolve()` reproduces the
  ignoring peak exactly;
- `pipe()` and `pipeline()` were already right;
- a transform that forgets its callback stalls without an error (`settled=false, error=null`);
- calling the callback twice is an error (`Callback called multiple times`).

## Exit codes

| code | meaning |
| ---- | ------- |
| 0 | the bounded mode stayed bounded (or the command succeeded) |
| 1 | the bounded mode exceeded `--max-peak-chunks` |
| 2 | the input was unusable (bad number, missing value, unknown command) |

`compare` is the gate: run it in CI with a bound you are willing to defend. A producer that
starts ignoring refusals turns that line into `bounded    NO` without touching a test.

## Layout

```
src/types.ts      Measure, SinkOptions, chunkSeries, kib, ratio
src/sink.ts       slowSink: a writable that takes latencyMs per chunk
src/pipeline.ts   run(mode, chunks, options): ignoring | awaiting | honoring | pipeline
src/transform.ts  ForgettingTransform, TwiceTransform, drive() — the two hang shapes
src/demo.ts       the five stories
src/main.ts       compare, demo, --version, --help
src/selftest.ts   offline checks over everything above
tests/            node:test suites for the pieces, the modes, the transforms and the cli
```

## What this stack does not do

It does not benchmark throughput: the sink's latency is the clock, and CI runners are shared.
It does not tell you where to put a backpressure boundary in your own program; it shows what
each boundary costs, measured on the sink you bring.
