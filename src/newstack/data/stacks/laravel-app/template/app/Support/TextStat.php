<?php

declare(strict_types=1);

namespace App\Support;

/**
 * Pure text statistics: no I/O, no framework, no globals.
 *
 * The numbers match POSIX `wc` — lines are newline characters, words are runs
 * of non-whitespace, bytes are the raw string length — so the route, the shell
 * and the unit tests all agree on what a count means.
 */
final class TextStat
{
    /**
     * @return array{lines: int, words: int, bytes: int}
     */
    public static function of(string $text): array
    {
        return [
            'lines' => substr_count($text, "\n"),
            'words' => (int) preg_match_all('/\S+/', $text),
            'bytes' => strlen($text),
        ];
    }
}
