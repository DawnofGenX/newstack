<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Cli;
use PHPUnit\Framework\TestCase;

final class CliTest extends TestCase
{
    /**
     * @param list<string> $argv
     *
     * @return array{0: string, 1: string, 2: int}
     */
    private function capture(array $argv, string $stdin = ''): array
    {
        $in = fopen('php://memory', 'r+');
        fwrite($in, $stdin);
        rewind($in);
        $out = fopen('php://memory', 'r+');
        $err = fopen('php://memory', 'r+');

        $status = (new Cli('table'))->run($argv, $in, $out, $err);

        rewind($out);
        rewind($err);

        return [(string) stream_get_contents($out), (string) stream_get_contents($err), $status];
    }

    public function testRendersStdinAsATable(): void
    {
        [$stdout, , $status] = $this->capture([], "a,b\n1,2\n");
        self::assertSame(0, $status);
        self::assertStringContainsString('| a | b |', $stdout);
        self::assertStringContainsString('| 1 | 2 |', $stdout);
    }

    public function testHeaderAndAlignment(): void
    {
        [$stdout, , $status] = $this->capture(['--header', '--align', 'right'], "name,score\nalice,3\n");
        self::assertSame(0, $status);
        self::assertStringContainsString('|  name | score |', $stdout);
        self::assertStringContainsString('| alice |     3 |', $stdout);
    }

    public function testPerColumnAlignment(): void
    {
        [$stdout, , $status] = $this->capture(['--align-column', '1=right'], "a,bb\nxxx,1\n");
        self::assertSame(0, $status);
        self::assertStringContainsString('| xxx |  1 |', $stdout);
    }

    public function testTabDelimiter(): void
    {
        [$stdout, , $status] = $this->capture(['--delimiter', 'tab'], "a\tb\n");
        self::assertSame(0, $status);
        self::assertStringContainsString('| a | b |', $stdout);
    }

    public function testMaxWidthTruncates(): void
    {
        [$stdout] = $this->capture(['--max-width', '4'], "abcdef\n");
        self::assertStringContainsString('abc…', $stdout);
    }

    public function testNoBorder(): void
    {
        [$stdout] = $this->capture(['--border', 'none'], "a,b\n");
        self::assertSame("a  b\n", $stdout);
    }

    public function testUsageErrorsExitTwo(): void
    {
        self::assertSame(2, $this->capture(['--bogus'])[2]);
        self::assertSame(2, $this->capture(['--delimiter'])[2]);
        self::assertSame(2, $this->capture(['--align'])[2]);
        self::assertSame(2, $this->capture(['--align-column', 'x'])[2]);
    }

    public function testEmptyInputExitsOne(): void
    {
        [$stdout, $stderr, $status] = $this->capture([]);
        self::assertSame(1, $status);
        self::assertSame('', $stdout);
        self::assertStringContainsString('no rows', $stderr);
    }

    public function testUnreadableFileExitsOne(): void
    {
        [, $stderr, $status] = $this->capture(['does-not-exist.csv']);
        self::assertSame(1, $status);
        self::assertStringContainsString('cannot read', $stderr);
    }

    public function testHelpExitsZero(): void
    {
        [$stdout, , $status] = $this->capture(['--help']);
        self::assertSame(0, $status);
        self::assertStringContainsString('--border', $stdout);
    }
}
