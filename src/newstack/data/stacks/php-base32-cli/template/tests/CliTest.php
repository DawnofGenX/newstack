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

    /**
     * @param list<string> $arguments
     */
    private function runCli(array $arguments, string $stdin = ''): int
    {
        $input = fopen('php://memory', 'w+b');
        fwrite($input, $stdin);
        rewind($input);

        return (new Cli('{{ npm_name }}'))->run($arguments, $input, $this->stdout, $this->stderr);
    }

    private function stdout(): string
    {
        rewind($this->stdout);

        return (string) stream_get_contents($this->stdout);
    }

    public function testEncodeReadsStdin(): void
    {
        self::assertSame(0, $this->runCli(['encode'], 'foobar'));
        self::assertSame('MZXW6YTBOI======' . PHP_EOL, $this->stdout());
    }

    public function testEncodeHonoursNoPad(): void
    {
        self::assertSame(0, $this->runCli(['encode', '--no-pad'], 'foobar'));
        self::assertSame('MZXW6YTBOI' . PHP_EOL, $this->stdout());
    }

    public function testDecodeRoundTripsStdin(): void
    {
        self::assertSame(0, $this->runCli(['decode'], 'MZXW6YTBOI======'));
        self::assertSame('foobar' . PHP_EOL, $this->stdout());
    }

    public function testHelpExitsZero(): void
    {
        self::assertSame(0, $this->runCli(['--help']));
        self::assertStringContainsString('usage:', $this->stdout());
    }

    public function testUnknownCommandExitsTwo(): void
    {
        self::assertSame(2, $this->runCli(['bogus']));
    }

    public function testMissingFileExitsOne(): void
    {
        self::assertSame(1, $this->runCli(['encode', 'does-not-exist.txt']));
    }

    public function testInvalidInputExitsOne(): void
    {
        self::assertSame(1, $this->runCli(['decode'], 'MZXW1YTB'));
    }
}
