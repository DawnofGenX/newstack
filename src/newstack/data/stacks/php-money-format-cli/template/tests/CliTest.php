<?php
declare(strict_types=1);
namespace {{ package_name }}\Tests;
use {{ package_name }}\Cli;
use {{ package_name }}\Money;
use PHPUnit\Framework\TestCase;
final class MoneyTest extends TestCase
{
    public function testFormatUsd(): void { self::assertSame('$12.34', (new Money('12.34'))->format()); }
    public function testAllocateInvariant(): void
    {
        $parts = Money::allocate(100, 3);
        self::assertSame([34, 33, 33], $parts);
        self::assertSame(100, array_sum($parts));
    }
}
final class CliTest extends TestCase
{
    private function capture(array $argv): array
    {
        $in = fopen('php://memory', 'r+');
        $out = fopen('php://memory', 'r+');
        $err = fopen('php://memory', 'r+');
        $status = (new Cli('money'))->run($argv, $in, $out, $err);
        rewind($out); rewind($err);
        return [(string) stream_get_contents($out), (string) stream_get_contents($err), $status];
    }
    public function testFormat(): void
    {
        [$stdout, , $code] = $this->capture(['format', '12.34']);
        self::assertSame(0, $code);
        self::assertSame("\$12.34\n", $stdout);
    }
    public function testAllocate(): void
    {
        [$stdout, , $code] = $this->capture(['allocate', '1.00', '3']);
        self::assertSame(0, $code);
        self::assertSame("0.34,0.33,0.33\n", $stdout);
    }
    public function testUsageErrorExitsTwo(): void
    {
        [, , $code] = $this->capture([]);
        self::assertSame(2, $code);
    }
    public function testHelpExitsZero(): void
    {
        [$stdout, , $code] = $this->capture(['--help']);
        self::assertSame(0, $code);
        self::assertStringContainsString('Usage:', $stdout);
    }
}
