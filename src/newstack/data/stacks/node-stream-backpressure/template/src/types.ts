export interface Measure {
  readonly mode: string;
  readonly chunks: number;
  readonly bytes: number;
  readonly peakBuffered: number;
  readonly waits: number;
  readonly stalls: number;
  readonly ms: number;
}

export interface SinkOptions {
  readonly highWaterMark: number;
  readonly latencyMs: number;
}

export const CHUNK_BYTES = 16 * 1024;

export function chunkSeries(count: number, size = CHUNK_BYTES): Uint8Array[] {
  const chunks: Uint8Array[] = [];
  for (let index = 0; index < count; index += 1) {
    const chunk = new Uint8Array(size);
    chunk.fill(index % 251);
    chunks.push(chunk);
  }
  return chunks;
}

export function kib(bytes: number): string {
  return `${(bytes / 1024).toFixed(1)} KiB`;
}

export function ratio(peak: number, chunk: number): string {
  return `${(peak / chunk).toFixed(1)}x a chunk`;
}
