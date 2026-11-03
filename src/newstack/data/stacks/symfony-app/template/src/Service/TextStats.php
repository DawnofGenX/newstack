<?php

declare(strict_types=1);

namespace {{ package_name }}\Service;

/**
 * Pure counting logic: no reading, no printing, so it is trivially testable.
 */
final class TextStats
{
    /**
     * Count newline terminators, runs of non-whitespace, and raw bytes.
     *
     * Bytes are counted as bytes rather than characters on purpose: that is what
     * `wc -c` reports, and it stays correct for input that is not valid UTF-8.
     */
    public function count(string $text): Stats
    {
        $trimmed = trim($text);
        $words = 0;
        if ($trimmed !== '') {
            $words = count(preg_split('/\s+/', $trimmed) ?: []);
        }

        return new Stats(
            substr_count($text, "\n"),
            $words,
            strlen($text),
        );
    }
}
