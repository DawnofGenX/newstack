// Pure CRC-32C (Castagnoli) implementation.
const POLY = 0x82f63b78 >>> 0;
const TABLE = new Uint32Array(256);
for (let i = 0; i < 256; i++) {
  let c = i;
  for (let k = 0; k < 8; k++) {
    c = (c & 1) ? (POLY ^ (c >>> 1)) : (c >>> 1);
  }
  TABLE[i] = c >>> 0;
}

export function crc32c(input) {
  const buf = Buffer.isBuffer(input) ? input : Buffer.from(String(input), "utf8");
  let crc = 0xffffffff;
  for (let i = 0; i < buf.length; i++) {
    crc = TABLE[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}