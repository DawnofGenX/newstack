import { describe, expect, it } from "bun:test";
import { crc32, digest, digestText, formatLine, parseChecksums, verify } from "../src/hash/hash.ts";

const HELLO = new TextEncoder().encode("hello");
const EMPTY = new Uint8Array();

describe("digest", () => {
  it("pins the sha256 of hello", () => {
    expect(digest(HELLO, "sha256")).toBe(
      "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824",
    );
  });

  it("pins the sha1 and md5 of hello", () => {
    expect(digest(HELLO, "sha1")).toBe("aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d");
    expect(digest(HELLO, "md5")).toBe("5d41402abc4b2a76b9719d911017c592");
  });

  it("defaults to sha256", () => {
    expect(digest(HELLO)).toBe(digest(HELLO, "sha256"));
  });

  it("pins the digests of the empty input", () => {
    expect(digest(EMPTY, "sha256")).toBe(
      "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    );
    expect(digest(EMPTY, "sha1")).toBe("da39a3ee5e6b4b0d3255bfef95601890afd80709");
    expect(digest(EMPTY, "md5")).toBe("d41d8cd98f00b204e9800998ecf8427e");
    expect(crc32(EMPTY)).toBe(0);
  });

  it("digestText hashes the utf-8 bytes", () => {
    expect(digestText("hello")).toBe(digest(HELLO));
    expect(digestText("héllo").length).toBe(64);
  });
});

describe("crc32", () => {
  it("pins the standard check value", () => {
    expect(crc32(new TextEncoder().encode("123456789")).toString(16)).toBe("cbf43926");
  });

  it("pins hello", () => {
    expect(crc32(HELLO).toString(16)).toBe("3610a686");
  });

  it("is zero padded to eight hex characters when formatted", () => {
    expect(digest(new TextEncoder().encode("00000000"), "crc32").length).toBe(8);
  });
});

describe("parseChecksums", () => {
  it("reads digest and name pairs separated by two spaces", () => {
    expect(parseChecksums("abc123  a.txt\n")).toEqual([{ digest: "abc123", name: "a.txt" }]);
  });

  it("tolerates one space, tabs and binary mode stars", () => {
    expect(parseChecksums("abc123 a.txt\n")).toEqual([{ digest: "abc123", name: "a.txt" }]);
    expect(parseChecksums("abc123\tb.txt\n")).toEqual([{ digest: "abc123", name: "b.txt" }]);
    expect(parseChecksums("abc123 *c.txt\n")).toEqual([{ digest: "abc123", name: "c.txt" }]);
  });

  it("lowercases the digest", () => {
    expect(parseChecksums("ABC123  a.txt\n")[0].digest).toBe("abc123");
  });

  it("skips blank lines and comments", () => {
    expect(parseChecksums("\n# note\nabc  a\n")).toEqual([{ digest: "abc", name: "a" }]);
  });

  it("rejects a line with no name", () => {
    expect(() => parseChecksums("abc123\n")).toThrow("cannot parse checksum line");
  });
});

describe("verify", () => {
  const entries = parseChecksums("abc123  a.txt\nfff  b.txt\n");

  it("accepts an exact match and rejects a mismatch", () => {
    const results = verify(entries, (name) => (name === "a.txt" ? "abc123" : "eeee"));
    expect(results.map((result) => result.ok)).toEqual([true, false]);
    expect(results[1].expected).toBe("fff");
    expect(results[1].actual).toBe("eeee");
  });

  it("accepts a digest given as a prefix", () => {
    const results = verify(entries, () => "abc123456");
    expect(results[0].ok).toBe(true);
  });
});

describe("formatLine", () => {
  it("uses two spaces like sha256sum", () => {
    expect(formatLine("abc", "a.txt")).toBe("abc  a.txt");
  });
});
