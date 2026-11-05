/**
 * Counting a stream, not a string.
 *
 * Both shortcuts that look obvious are wrong, and wrong silently:
 *
 * - `chunk.toString()` per read turns a UTF-8 character that straddles a buffer
 *   boundary into two replacement characters, so `bytes` is right and `words` is not.
 * - Counting `/\S+/g` matches per chunk splits a word that straddles a boundary into
 *   two words, so a file read in 64 KiB pieces counts more words than the same file
 *   passed to the program on one line.
 */
export interface Counts {
  lines: number;
  words: number;
  bytes: number;
}

export const ZERO: Counts = { lines: 0, words: 0, bytes: 0 };

export function add(left: Counts, right: Counts): Counts {
  return {
    lines: left.lines + right.lines,
    words: left.words + right.words,
    bytes: left.bytes + right.bytes,
  };
}

export class Counter {
  bytes = 0;
  private newlines = 0;
  private words = 0;
  /** The trailing word of the last chunk: it may continue in the next one. */
  private carry = "";
  private ended = false;
  private trailingNewline = true;
  private readonly decoder = new TextDecoder("utf-8");

  push(chunk: Uint8Array): void {
    if (this.ended) throw new Error("push() after end()");
    this.bytes += chunk.length;
    // stream: true keeps an incomplete trailing sequence inside the decoder.
    this.consume(this.decoder.decode(chunk, { stream: true }));
  }

  end(): Counts {
    if (this.ended) throw new Error("end() twice");
    this.ended = true;
    this.consume(this.decoder.decode());
    if (this.carry !== "") {
      this.words += 1;
      this.carry = "";
    }
    // Logical lines: "a\nb" is two lines to every editor and one to `wc -l`.
    const partial = this.bytes > 0 && !this.trailingNewline ? 1 : 0;
    return { lines: this.newlines + partial, words: this.words, bytes: this.bytes };
  }

  private consume(text: string): void {
    if (text === "") return;
    this.trailingNewline = text.endsWith("\n");
    for (const character of text) {
      if (character === "\n") this.newlines += 1;
    }
    const joined = this.carry + text;
    const matches = joined.match(/\S+/g) ?? [];
    const last = matches[matches.length - 1];
    const open = last !== undefined && !/\s/.test(joined.charAt(joined.length - 1));
    this.words += open ? matches.length - 1 : matches.length;
    this.carry = open && last !== undefined ? last : "";
  }
}

/** Convenience for tests and the selftest: the counts of one in-memory buffer. */
export function countBytes(chunk: Uint8Array): Counts {
  const counter = new Counter();
  counter.push(chunk);
  return counter.end();
}
