<?php

declare(strict_types=1);

namespace {{ package_name }}\Service;

/**
 * Line / word / byte counts for a piece of text.
 */
final readonly class Stats
{
    public function __construct(
        public int $lines,
        public int $words,
        public int $bytes,
    ) {
    }
}
