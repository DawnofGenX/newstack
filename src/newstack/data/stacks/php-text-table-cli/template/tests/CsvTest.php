<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Csv;
use InvalidArgumentException;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

final class CsvTest extends TestCase
{
    /** @return iterable<string, array{string, string, list<list<string>>}> */
    public static function documents(): iterable
    {
        yield 'simple rows' => ["a,b\nc,d\n", ',', [['a', 'b'], ['c', 'd']]];
        yield 'no trailing newline' => ['a,b', ',', [['a', 'b']]];
        yield 'quoted comma' => ['"a,b",c', ',', [['a,b', 'c']]];
        yield 'doubled quotes' => ['"he said ""hi""",c', ',', [['he said "hi"', 'c']]];
        yield 'quoted newline' => ["\"a\nb\",c\n", ',', [["a\nb", 'c']]];
        yield 'crlf' => ["a,b\r\nc,d\r\n", ',', [['a', 'b'], ['c', 'd']]];
        yield 'tabs' => ["a\tb\n", "\t", [['a', 'b']]];
        yield 'empty field' => ['a,,c', ',', [['a', '', 'c']]];
    }

    #[DataProvider('documents')]
    /**
     * @param list<list<string>> $expected
     */
    public function testParses(string $text, string $delimiter, array $expected): void
    {
        self::assertSame($expected, Csv::parse($text, $delimiter));
    }

    public function testRejectsAnUnterminatedQuote(): void
    {
        $this->expectException(InvalidArgumentException::class);
        $this->expectExceptionMessage('unterminated quoted field');
        Csv::parse('"a,b', ',');
    }

    public function testRoundTripsThroughRender(): void
    {
        $rows = [['a,b', 'c'], ['say "hi"', 'x']];
        self::assertSame($rows, Csv::parse(Csv::render($rows), ','));
    }
}
