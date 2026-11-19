<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Bcrypt;
use {{ package_name }}\Cli;
use PHPUnit\Framework\TestCase;

final class BcryptTest extends TestCase
{
    public function testHashAndVerifyRoundTrip(): void
    {
        $hash = Bcrypt::hash('secret', 4);
        self::assertTrue(Bcrypt::verify('secret', $hash));
        self::assertFalse(Bcrypt::verify('wrong', $hash));
    }

    public function testFixedCostEmbedded(): void
    {
        $hash = Bcrypt::hash('secret', 4);
        self::assertStringStartsWith('$2y$04$', $hash);
    }
}

final class CliTest extends TestCase
{
    /**
     * @param list<string> $argv
     *
     * @return array{0: string, 1: string, 2: int}
     */
    private function capture(array $argv): array
    {
        $in = fopen('php://memory', 'r+');
        $out = fopen('php://memory', 'r+');
        $err = fopen('php://memory', 'r+');

        $status = (new Cli('bcrypt'))->run($argv, $in, $out, $err);

        rewind($out);
        rewind($err);

        return [(string) stream_get_contents($out), (string) stream_get_contents($err), $status];
    }

    public function testHashExitsZero(): void
    {
        [$stdout, , $code] = $this->capture(['hash', 'secret', '4']);
        self::assertSame(0, $code);
        self::assertStringStartsWith('$2y$', trim($stdout));
    }

    public function testVerifyMatch(): void
    {
        $hash = Bcrypt::hash('secret', 4);
        [$stdout, , $code] = $this->capture(['verify', 'secret', $hash]);
        self::assertSame(0, $code);
        self::assertSame("match\n", $stdout);
    }

    public function testVerifyMismatchExitsOne(): void
    {
        $hash = Bcrypt::hash('secret', 4);
        [$stdout, , $code] = $this->capture(['verify', 'wrong', $hash]);
        self::assertSame(1, $code);
        self::assertSame("mismatch\n", $stdout);
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