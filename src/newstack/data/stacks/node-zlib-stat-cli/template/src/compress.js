import { gunzipSync, gzipSync } from "node:zlib";

const GZIP_MAGIC_0 = 0x1f;
const GZIP_MAGIC_1 = 0x8b;

export function isGzip(buffer) {
  return buffer.length >= 2 && buffer[0] === GZIP_MAGIC_0 && buffer[1] === GZIP_MAGIC_1;
}

export function compress(buffer, { level = 6 } = {}) {
  if (!Number.isInteger(level) || level < 0 || level > 9) {
    throw new RangeError(`compression level must be an integer 0..9, got ${level}`);
  }
  return gzipSync(buffer, { level });
}

export function decompress(buffer) {
  if (!isGzip(buffer)) {
    throw new Error("input is not gzip data");
  }
  return gunzipSync(buffer);
}

export function stats(originalBytes, compressedBytes) {
  const ratio =
    originalBytes === 0 ? 0 : Math.round((compressedBytes / originalBytes) * 1000) / 1000;
  return {
    originalBytes,
    compressedBytes,
    savedBytes: originalBytes - compressedBytes,
    ratio,
  };
}

export function describe(buffer) {
  if (!isGzip(buffer)) {
    return { format: "unknown", compressed: false, bytes: buffer.length };
  }
  const flags = buffer[3] ?? 0;
  return {
    format: "gzip",
    compressed: true,
    bytes: buffer.length,
    filenameFlag: Boolean(flags & 0x08),
    commentFlag: Boolean(flags & 0x10),
  };
}

export function formatStats(entry) {
  return `input=${entry.originalBytes} bytes compressed=${entry.compressedBytes} bytes ratio=${entry.ratio} saved=${entry.savedBytes} bytes`;
}
