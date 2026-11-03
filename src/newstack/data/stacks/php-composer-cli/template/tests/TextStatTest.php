<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Counts;
use {{ package_name }}\TextStat;
use PHPUnit\Framework\TestCase;

final class TextStatTest extends TestCase
{
    public function testCountsLinesWordsAndBytes(): void
    {
        $counts = TextStat::count("one two\nthree\n");

        self::assertSame(2, $counts->lines);
        self::assertSame(3, $counts->words);
        self::assertSame(14, $counts->bytes);
    }

    public function testEmptyInputCountsNothing(): void
    {
        $counts = TextStat::count('');

        self::assertSame(0, $counts->lines);
        self::assertSame(0, $counts->words);
        self::assertSame(0, $counts->bytes);
    }

    public function testTrailingWhitespaceDoesNotStartAWord(): void
    {
        $counts = TextStat::count("  padded\ttext  \n");

        self::assertSame(1, $counts->lines);
        self::assertSame(2, $counts->words);
        self::assertSame(16, $counts->bytes);
    }

    public function testBytesAreBytesNotCharacters(): void
    {
        $counts = TextStat::count('héllo');

        self::assertSame(0, $counts->lines);
        self::assertSame(1, $counts->words);
        self::assertSame(6, $counts->bytes);
    }

    public function testCountsAreAdditive(): void
    {
        $total = TextStat::count("a b\n")->plus(TextStat::count("c\n"));

        self::assertInstanceOf(Counts::class, $total);
        self::assertSame(2, $total->lines);
        self::assertSame(3, $total->words);
        self::assertSame(6, $total->bytes);
    }
}
