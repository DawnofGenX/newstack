import { describe, expect, test } from "bun:test";
import {
  compare,
  format,
  fromHex,
  isUuid,
  parse,
  toHex,
  uuidV7,
} from "../src/uuid/format.ts";

const ZEROS = new Uint8Array(10);

describe("uuidV7", () => {
  test("packs the timestamp into the first 48 bits", () => {
    const bytes = uuidV7(0x0102_0304_0506, ZEROS);
    expect(toHex(bytes.slice(0, 6))).toBe("010203040506");
  });

  test("sets the version nibble and the rfc4122 variant", () => {
    const bytes = uuidV7(1_700_000_000_000, ZEROS);
    expect(bytes[6] >> 4).toBe(7);
    expect(bytes[8] & 0xc0).toBe(0x80);
  });

  test("keeps the random bytes it was given", () => {
    const random = new Uint8Array([0x0f, 0xab, 0x3f, 1, 2, 3, 4, 5, 6, 7]);
    const bytes = uuidV7(42, random);
    expect(bytes[6]).toBe(0x7f);
    expect(bytes[7]).toBe(0xab);
    expect(bytes[8]).toBe(0xbf);
    expect([...bytes.slice(9)]).toEqual([1, 2, 3, 4, 5, 6, 7]);
  });

  test("is deterministic for the same inputs", () => {
    const first = format(uuidV7(1_700_000_000_000, ZEROS));
    const second = format(uuidV7(1_700_000_000_000, ZEROS));
    expect(first).toBe(second);
    expect(first.startsWith("018bcfe5-6800-7")).toBe(true);
  });

  test("matches the canonical shape", () => {
    const text = format(uuidV7(1_700_000_000_000, new Uint8Array(10).fill(0x5a)));
    expect(text).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
  });

  test("rejects an out-of-range timestamp", () => {
    expect(() => uuidV7(2 ** 52, ZEROS)).toThrow(/out of range/);
    expect(() => uuidV7(-1, ZEROS)).toThrow(/out of range/);
  });

  test("rejects too few random bytes", () => {
    expect(() => uuidV7(1, new Uint8Array(9))).toThrow(/need 10 random bytes/);
  });
});

describe("parse", () => {
  const text = format(uuidV7(1_700_000_000_000, new Uint8Array(10).fill(0x11)));

  test("recovers the timestamp it was built from", () => {
    expect(parse(text).timestampMs).toBe(1_700_000_000_000);
  });

  test("reports version 7 and the rfc4122 variant", () => {
    const uuid = parse(text);
    expect(uuid.version).toBe(7);
    expect(uuid.variant).toBe(true);
  });

  test("accepts upper case and surrounding whitespace", () => {
    expect(parse(`  ${text.toUpperCase()}  `).text).toBe(text);
  });

  test("rejects a non-canonical string", () => {
    expect(() => parse("not-a-uuid")).toThrow(/not a canonical uuid/);
    expect(() => parse(text.replaceAll("-", ""))).toThrow(/not a canonical uuid/);
  });

  test("rejects an unsupported version", () => {
    const v9 = text.slice(0, 14) + "9" + text.slice(15);
    expect(() => parse(v9)).toThrow(/unsupported uuid version 9/);
  });

  test("has no timestamp for a v4 uuid", () => {
    const v4 = "5b1e6f9a-2f7c-4b6d-9c1e-0d5f2b8a7c31";
    const uuid = parse(v4);
    expect(uuid.version).toBe(4);
    expect(uuid.timestampMs).toBeNull();
  });
});

describe("helpers", () => {
  test("isUuid accepts v7 and v4 and rejects junk", () => {
    expect(isUuid(format(uuidV7(1, ZEROS)))).toBe(true);
    expect(isUuid("5b1e6f9a-2f7c-4b6d-9c1e-0d5f2b8a7c31")).toBe(true);
    expect(isUuid("5b1e6f9a-2f7c-9b6d-9c1e-0d5f2b8a7c31")).toBe(false);
    expect(isUuid("nope")).toBe(false);
  });

  test("fromHex rejects malformed input", () => {
    expect(() => fromHex("abc")).toThrow(/odd number/);
    expect(() => fromHex("zz")).toThrow(/invalid hex pair/);
  });

  test("compare orders by text, which is time order for v7", () => {
    const early = format(uuidV7(1_000, ZEROS));
    const late = format(uuidV7(2_000, ZEROS));
    expect(compare(early, late)).toBe(-1);
    expect(compare(late, early)).toBe(1);
    expect(compare(early, early)).toBe(0);
  });
});
