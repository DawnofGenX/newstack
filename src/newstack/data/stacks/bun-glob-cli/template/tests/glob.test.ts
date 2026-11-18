import { describe, expect, test } from "bun:test";
import { expandBraces, globToRegExp, matches, matchesAny, normalise } from "../src/glob/glob.ts";

describe("globToRegExp", () => {
  test("* stays inside one segment", () => {
    expect(matches("src/*.ts", "src/a.ts")).toBe(true);
    expect(matches("src/*.ts", "src/deep/a.ts")).toBe(false);
  });

  test("** crosses segments and matches zero of them", () => {
    expect(matches("**/*.ts", "a.ts")).toBe(true);
    expect(matches("**/*.ts", "a/b/c.ts")).toBe(true);
    expect(matches("src/**/test.ts", "src/test.ts")).toBe(true);
    expect(matches("src/**/test.ts", "src/a/b/test.ts")).toBe(true);
    expect(matches("src/**", "src/a/b/c.ts")).toBe(true);
  });

  test("? matches exactly one character and never a slash", () => {
    expect(matches("a?c.txt", "abc.txt")).toBe(true);
    expect(matches("a?c.txt", "ac.txt")).toBe(false);
    expect(matches("a?c", "a/c")).toBe(false);
  });

  test("character classes and negated classes", () => {
    expect(matches("file[0-9].txt", "file7.txt")).toBe(true);
    expect(matches("file[0-9].txt", "filea.txt")).toBe(false);
    expect(matches("file[!0-9].txt", "filea.txt")).toBe(true);
    expect(matches("file[!0-9].txt", "file7.txt")).toBe(false);
  });

  test("braces expand to alternatives, including nested ones", () => {
    expect(expandBraces("src/{a,b}/*.ts")).toEqual(["src/a/*.ts", "src/b/*.ts"]);
    expect(expandBraces("x.{js,{m,c}js}")).toEqual(["x.js", "x.mjs", "x.cjs"]);
    expect(matches("*.{js,ts}", "index.ts")).toBe(true);
    expect(matches("*.{js,ts}", "index.rb")).toBe(false);
  });

  test("regex metacharacters in the pattern are literals", () => {
    expect(matches("a+b(c).txt", "a+b(c).txt")).toBe(true);
    expect(matches("a+b(c).txt", "aab(c).txt")).toBe(false);
    expect(matches("v1.2.3", "v1x2x3")).toBe(false);
  });

  test("an unbalanced brace is a literal", () => {
    expect(matches("a{b", "a{b")).toBe(true);
  });

  test("the pattern is anchored at both ends", () => {
    expect(matches("b.ts", "a/b.ts")).toBe(false);
    expect(globToRegExp("b.ts").test("b.ts")).toBe(true);
  });
});

describe("helpers", () => {
  test("matchesAny is a disjunction", () => {
    expect(matchesAny(["*.md", "*.ts"], "readme.md")).toBe(true);
    expect(matchesAny(["*.md", "*.ts"], "readme.rb")).toBe(false);
    expect(matchesAny([], "readme.md")).toBe(false);
  });

  test("normalise strips ./ and trailing slashes", () => {
    expect(normalise("./a//b/")).toBe("a/b");
    expect(normalise("a/b")).toBe("a/b");
  });
});
