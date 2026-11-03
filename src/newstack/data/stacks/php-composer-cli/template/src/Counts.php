<?php

declare(strict_types=1);

namespace {{ package_name }};

/**
 * Line, word and byte counts for one input.
 *
 * Plain data with no I/O, so tests can assert on it directly.
 */
final readonly class Counts
{
    public function __construct(
        public int $lines,
        public int $words,
        public int $bytes,
    ) {
    }

    /** Sum of two counts, used for the multi-file total. */
    public function plus(self $other): self
    {
        return new self(
            $this->lines + $other->lines,
            $this->words + $other->words,
            $this->bytes + $other->bytes,
        );
    }
}
