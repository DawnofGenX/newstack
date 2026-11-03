import { describe, expect, it } from "bun:test";
import { add, count } from "../src/textstat/counts.ts";

describe("counts", () => {
  it("empty input has no lines, words or bytes", () => {
    expect(count("")).toEqual({ lines: 0, words: 0, bytes: 0 });
  });

  it("a trailing newline counts as a line", () => {
    expect(count("hello\n")).toEqual({ lines: 1, words: 1, bytes: 6 });
  });

  it("input without a trailing newline has no counted line", () => {
    expect(count("hello")).toEqual({ lines: 0, words: 1, bytes: 5 });
  });

  it("runs of whitespace separate words without adding empty ones", () => {
    expect(count("  a   b  ")).toEqual({ lines: 0, words: 2, bytes: 9 });
  });

  it("tabs and carriage returns are whitespace, newline ends a line", () => {
    expect(count("\ta\r\nb\n")).toEqual({ lines: 2, words: 2, bytes: 6 });
  });

  it("every line is counted once", () => {
    expect(count("one two\nthree\n")).toEqual({ lines: 2, words: 3, bytes: 14 });
  });

  it("blank lines count as lines but not as words", () => {
    expect(count("a\n\n\nb\n")).toEqual({ lines: 4, words: 2, bytes: 6 });
  });

  it("multi-byte characters count as their UTF-8 byte length", () => {
    expect(count("héllo\n")).toEqual({ lines: 1, words: 1, bytes: 7 });
  });

  it("totals add field by field", () => {
    expect(add(count("a b\n"), count("c\n"))).toEqual({ lines: 2, words: 3, bytes: 6 });
  });
});
