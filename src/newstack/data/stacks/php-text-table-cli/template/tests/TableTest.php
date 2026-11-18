<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Table;
use InvalidArgumentException;
use PHPUnit\Framework\TestCase;

final class TableTest extends TestCase
{
    public function testRendersAnAsciiTableWithHeaders(): void
    {
        $table = Table::make([['alice', '3'], ['bob', '12']], ['name', 'score']);

        self::assertSame(
            implode("\n", [
                '+-------+-------+',
                '| name  | score |',
                '+-------+-------+',
                '| alice | 3     |',
                '| bob   | 12    |',
                '+-------+-------+',
                '',
            ]),
            $table->render(),
        );
    }

    public function testRightAlignsColumns(): void
    {
        $table = Table::make([['alice', '3'], ['bob', '12']], ['name', 'score'])
            ->alignments([Table::ALIGN_LEFT, Table::ALIGN_RIGHT]);

        self::assertStringContainsString('|    12 |', $table->render());
        self::assertStringContainsString('|     3 |', $table->render());
    }

    public function testCentersColumns(): void
    {
        $table = Table::make([['ab']], ['title'])->alignments([Table::ALIGN_CENTER]);
        self::assertStringContainsString('| title |', $table->render());
        self::assertStringContainsString('|  ab   |', $table->render());
    }

    public function testUnicodeBorder(): void
    {
        $rendered = Table::make([['a']], ['h'])->border(Table::BORDER_UNICODE)->render();
        self::assertStringContainsString('┌', $rendered) ;
        self::assertStringContainsString('│ a │', $rendered);
    }

    public function testNoBorderSeparatesWithTwoSpaces(): void
    {
        $rendered = Table::make([['alice', '3']], ['name', 'score'])->border(Table::BORDER_NONE)->render();
        self::assertSame("name   score\nalice  3\n", $rendered);
    }

    public function testTruncatesToMaxWidth(): void
    {
        $rendered = Table::make([['abcdefgh']])->maxWidth(5)->render();
        self::assertStringContainsString('abcd…', $rendered);
        self::assertStringNotContainsString('abcdefgh', $rendered);
    }

    public function testWideCharactersKeepTheBordersAligned(): void
    {
        $rendered = Table::make([['日本語', 'x']], ['name', 'flag'])->render();
        $lines = explode("\n", trim($rendered));
        $widths = array_map(static fn (string $line): int => mb_strwidth($line, 'UTF-8'), $lines);
        self::assertCount(1, array_unique($widths), 'every line of the table must be the same width');
    }

    public function testAnEmptyTableRendersNothing(): void
    {
        self::assertSame('', Table::make([])->render());
    }

    public function testRejectsAnUnknownBorder(): void
    {
        $this->expectException(InvalidArgumentException::class);
        Table::make([['a']])->border('double');
    }

    public function testRejectsAnUnknownAlignment(): void
    {
        $this->expectException(InvalidArgumentException::class);
        Table::make([['a']])->alignments(['justify']);
    }
}
