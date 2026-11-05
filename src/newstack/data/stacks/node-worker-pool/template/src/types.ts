export type JobKind = "sum" | "spin" | "checksum" | "boom" | "exit";

export interface Job {
  readonly id: number;
  readonly kind: JobKind;
  readonly values?: readonly number[];
  readonly ms?: number;
  readonly buffer?: ArrayBuffer;
  readonly code?: number;
}

export interface RemoteError {
  readonly message: string;
  readonly stack: string;
  readonly name: string;
}

export interface JobResult {
  readonly id: number;
  readonly ok: boolean;
  readonly value?: unknown;
  readonly buffer?: ArrayBuffer;
  readonly error?: RemoteError;
  readonly threadId?: number;
}

export interface PoolStats {
  readonly size: number;
  readonly spawns: number;
  readonly completed: number;
  readonly failed: number;
  readonly replaced: number;
  readonly queued: number;
  readonly peakQueue: number;
  readonly busy: number;
  readonly idle: number;
}

export interface CloseReport {
  readonly completed: number;
  readonly failed: number;
  readonly refused: number;
  readonly spawns: number;
  readonly replaced: number;
}

export function kib(bytes: number): string {
  return `${(bytes / 1024).toFixed(1)} KiB`;
}
