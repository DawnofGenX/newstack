<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Cli;
use PHPUnit\Framework\TestCase;

final class CliTest extends TestCase
{
    /** @var resource */
    private $stdout;

    /** @var resource */
    private $stderr;

    protected function setUp(): void
    {
        $this->stdout = fopen('php://memory', 'w+b');
        $this->stderr = fopen('php://memory', 'w+b');
    }

    protected function tearDown(): void
    {
        fclose($this->stdout);
        fclose($this->stderr);
    }

    private function stdout(): string
    {
        rewind($this->stdout);

        return (string) stream_get_contents($this->stdout);
    }

    private function stderr(): string
    {
        rewind($this->stderr);

        return (string) stream_get_contents($this->stderr);
    }

    /**
     * @param list<string> $args
     */
    private function runCli(array $args, string $stdin = ''): int
    {
        $input = fopen('php://memory', 'w+b');
        fwrite($input, $stdin);
        rewind($input);

        return (new Cli('{{ npm_name }}'))->run($args, $input, $this->stdout, $this->stderr);
    }

    private function makeFile(string $contents): string
    {
        $path = (string) tempnam(sys_get_temp_dir(), 'textstat-');
        file_put_contents($path, $contents);

        return $path;
    }

    public function testHelpExitsZeroAndPrintsUsage(): void
    {
        $code = $this->runCli(['--help'], 'ignored');

        self::assertSame(0, $code);
        self::assertStringContainsString('usage: {{ npm_name }}', $this->stdout());
        self::assertSame('', $this->stderr());
    }

    public function testUnknownFlagExitsTwo(): void
    {
        $code = $this->runCli(['--bogus']);

        self::assertSame(2, $code);
        self::assertStringContainsString("error: unknown option '--bogus'", $this->stderr());
        self::assertStringContainsString('usage: {{ npm_name }}', $this->stderr());
    }

    public function testMissingFileExitsOne(): void
    {
        $code = $this->runCli([__DIR__ . '/does-not-exist.txt']);

        self::assertSame(1, $code);
        self::assertStringContainsString('does-not-exist.txt', $this->stderr());
    }

    public function testCountsAFileAndPrintsItsName(): void
    {
        $path = $this->makeFile("one two\nthree\n");

        try {
            $code = $this->runCli([$path]);
        } finally {
            unlink($path);
        }

        self::assertSame(0, $code);
        self::assertMatchesRegularExpression('/^2\s+3\s+14\s+\S+$/', trim($this->stdout()));
    }

    public function testReadsStandardInputWhenNoFileIsGiven(): void
    {
        $code = $this->runCli(['-w'], "alpha beta gamma\n");

        self::assertSame(0, $code);
        self::assertSame('       3' . PHP_EOL, $this->stdout());
    }

    public function testMultipleFilesPrintATotal(): void
    {
        $first = $this->makeFile("a b\n");
        $second = $this->makeFile("c\n");

        try {
            $code = $this->runCli(['-l', $first, $second]);
        } finally {
            unlink($first);
            unlink($second);
        }

        self::assertSame(0, $code);
        $lines = array_values(array_filter(explode(PHP_EOL, $this->stdout())));
        self::assertCount(3, $lines);
        self::assertStringEndsWith('2 total', $lines[2]);
    }

    public function testUnreadableFileStillReportsTheOthers(): void
    {
        $good = $this->makeFile("a\n");

        try {
            $code = $this->runCli(['-l', $good, __DIR__ . '/nope.txt']);
        } finally {
            unlink($good);
        }

        self::assertSame(1, $code);
        self::assertStringContainsString("error: cannot open", $this->stderr());
        self::assertStringContainsString('1', $this->stdout());
    }
}
