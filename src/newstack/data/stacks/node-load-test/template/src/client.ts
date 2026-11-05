//! The load generator: fixed number of requests, N workers, one keep-alive agent.

import http from "node:http";
import https from "node:https";
import type { Sample } from "./types.js";

export interface LoadOptions {
  readonly url: string;
  readonly requests: number;
  readonly concurrency: number;
  readonly timeoutMs?: number;
}

export interface LoadResult {
  readonly samples: Sample[];
  readonly wallMs: number;
}

interface Outcome {
  readonly status: number;
  readonly error?: string;
}

function attempt(
  target: URL,
  agent: http.Agent | https.Agent,
  timeoutMs: number,
): Promise<Outcome> {
  return new Promise((resolve) => {
    const library = target.protocol === "https:" ? https : http;
    const request = library.request(
      target,
      { method: "GET", agent, headers: { "user-agent": "load-test" } },
      (response) => {
        // Drain the body. Without this the socket is never handed back to the
        // agent, so a "keep-alive" run silently opens one connection per request
        // and the numbers describe connection setup rather than the server.
        response.resume();
        response.on("end", () => resolve({ status: response.statusCode ?? 0 }));
        response.on("error", (error: Error) =>
          resolve({ status: response.statusCode ?? 0, error: error.message }),
        );
      },
    );
    request.setTimeout(timeoutMs, () => {
      request.destroy(new Error(`timeout after ${timeoutMs} ms`));
    });
    request.on("error", (error: Error) => resolve({ status: 0, error: error.message }));
    request.end();
  });
}

/** Fire `requests` GETs with `concurrency` workers and time every one of them.
 *
 * Latency starts at `dueAt` - the instant the request was allowed to start -
 * which is when the client began waiting, not when a free socket appeared.
 */
export async function load(options: LoadOptions): Promise<LoadResult> {
  if (options.requests < 1) throw new RangeError(`requests must be at least 1, got ${options.requests}`);
  if (options.concurrency < 1) {
    throw new RangeError(`concurrency must be at least 1, got ${options.concurrency}`);
  }
  const target = new URL(options.url);
  const timeoutMs = options.timeoutMs ?? 5000;
  const agent =
    target.protocol === "https:"
      ? new https.Agent({ keepAlive: true, maxSockets: options.concurrency })
      : new http.Agent({ keepAlive: true, maxSockets: options.concurrency });

  const samples: Sample[] = [];
  let next = 0;
  const started = process.hrtime.bigint();

  const worker = async (): Promise<void> => {
    for (;;) {
      const index = next;
      next += 1;
      if (index >= options.requests) return;
      const dueAt = process.hrtime.bigint();
      const outcome = await attempt(target, agent, timeoutMs);
      const latencyMs = Number(process.hrtime.bigint() - dueAt) / 1e6;
      const complete = outcome.error === undefined;
      const ok = complete && outcome.status >= 200 && outcome.status < 400;
      const sample: Sample = complete
        ? { index, dueAt, latencyMs, status: outcome.status, ok }
        : { index, dueAt, latencyMs, status: outcome.status, ok, error: outcome.error as string };
      samples.push(sample);
    }
  };

  await Promise.all(Array.from({ length: options.concurrency }, () => worker()));
  agent.destroy();
  return { samples, wallMs: Number(process.hrtime.bigint() - started) / 1e6 };
}
