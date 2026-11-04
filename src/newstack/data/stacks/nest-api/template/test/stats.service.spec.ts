import { StatsService } from "../src/stats/stats.service.js";

describe("StatsService", () => {
  const service = new StatsService();

  it("counts a single line", () => {
    expect(service.count("hello world")).toEqual({ lines: 0, words: 2, bytes: 11 });
  });

  it("counts newline-terminated lines like wc -l", () => {
    expect(service.count("a\nb\n")).toEqual({ lines: 2, words: 2, bytes: 4 });
  });

  it("does not count an unterminated final line", () => {
    expect(service.count("a\nb")).toEqual({ lines: 1, words: 2, bytes: 3 });
  });

  it("counts empty text as zero", () => {
    expect(service.count("")).toEqual({ lines: 0, words: 0, bytes: 0 });
  });

  it("counts UTF-8 bytes, not characters", () => {
    expect(service.count("héllo")).toEqual({ lines: 0, words: 1, bytes: 6 });
  });

  it("splits words on any whitespace run", () => {
    expect(service.count("  one\ttwo\nthree  ")).toEqual({
      lines: 1,
      words: 3,
      bytes: 17,
    });
  });
});
