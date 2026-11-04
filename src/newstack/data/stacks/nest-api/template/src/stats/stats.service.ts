import { Injectable } from "@nestjs/common";

export interface TextStats {
  lines: number;
  words: number;
  bytes: number;
}

/**
 * wc-style counts for a piece of text:
 * - lines: newline characters, like `wc -l`
 * - words: maximal runs of non-whitespace characters, like `wc -w`
 * - bytes: UTF-8 encoded length, like `wc -c`
 */
@Injectable()
export class StatsService {
  count(text: string): TextStats {
    const lines = (text.match(/\n/g) ?? []).length;
    const words = text.split(/\s+/).filter((part) => part.length > 0).length;
    const bytes = Buffer.byteLength(text, "utf8");
    return { lines, words, bytes };
  }
}
