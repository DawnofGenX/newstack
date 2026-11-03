<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Service\TextStats;
use PHPUnit\Framework\TestCase;

final class TextStatsTest extends TestCase
{
    private TextStats $stats;

    protected function setUp(): void
    {
        $this->stats = new TextStats();
    }

    public function testCountsLinesWordsAndBytes(): void
    {
        $counts = $this->stats->count("one two\nthree\n");

        self::assertSame(2, $counts->lines);
        self::assertSame(3, $counts->words);
        self::assertSame(14, $counts->bytes);
    }

    public function testEmptyInputCountsNothing(): void
    {
        $counts = $this->stats->count('');

        self::assertSame(0, $counts->lines);
        self::assertSame(0, $counts->words);
        self::assertSame(0, $counts->bytes);
    }

    public function testTrailingWhitespaceDoesNotStartAWord(): void
    {
        $counts = $this->stats->count("  padded\ttext  \n");

        self::assertSame(1, $counts->lines);
        self::assertSame(2, $counts->words);
        self::assertSame(16, $counts->bytes);
    }

    public function testBytesAreBytesNotCharacters(): void
    {
        $counts = $this->stats->count('héllo');

        self::assertSame(0, $counts->lines);
        self::assertSame(1, $counts->words);
        self::assertSame(6, $counts->bytes);
    }
}
