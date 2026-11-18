<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Cli;
use PHPUnit\Framework\TestCase;

final class CliTest extends TestCase
{
    /** @param list<string> $argv */
    private function capture(array $argv): array
    {
        $stdout = fopen('php://memory', 'w+');
        $stderr = fopen('php://memory', 'w+');
        $stdin = fopen('php://memory', 'r');
        $code = (new Cli('{{ npm_name }}'))->run($argv, $stdin, $stdout, $stderr);
        rewind($stdout);
        rewind($stderr);

        return [stream_get_contents($stdout), stream_get_contents($stderr), $code];
    }

    public function testParsePrintsJson(): void
    {
        [$stdout, , $code] = $this->capture(['parse', 'https://example.com/a?x=1']);

        self::assertSame(0, $code);
        $decoded = json_decode(trim($stdout), true, flags: JSON_THROW_ON_ERROR);
        self::assertSame('https', $decoded['scheme']);
        self::assertSame('example.com', $decoded['host']);
        self::assertSame('x=1', $decoded['query']);
    }

    public function testNormalizePrintsTheUrl(): void
    {
        [$stdout, , $code] = $this->capture(['normalize', 'HTTP://Example.COM:80/a/./b/../c']);

        self::assertSame(0, $code);
        self::assertSame('http://example.com/a/c', trim($stdout));
    }

    public function testEncodeAndDecode(): void
    {
        [$encoded, , $code] = $this->capture(['encode', 'a b&c']);
        self::assertSame(0, $code);
        self::assertSame('a%20b%26c', trim($encoded));

        [$decoded, , $code] = $this->capture(['decode', 'a%20b%26c']);
        self::assertSame(0, $code);
        self::assertSame('a b&c', trim($decoded));
    }

    public function testQueryReplacesAParameter(): void
    {
        [$stdout, , $code] = $this->capture(['query', 'https://example.com/a?x=1&y=2', 'y=9', 'z=3']);

        self::assertSame(0, $code);
        self::assertSame('https://example.com/a?x=1&y=9&z=3', trim($stdout));
    }

    public function testNoCommandIsAUsageError(): void
    {
        [$stdout, $stderr, $code] = $this->capture([]);

        self::assertSame(2, $code);
        self::assertSame('', $stdout);
        self::assertStringContainsString('no command given', $stderr);
    }

    public function testAnUnknownCommandIsAUsageError(): void
    {
        [, $stderr, $code] = $this->capture(['frobnicate', 'x']);

        self::assertSame(2, $code);
        self::assertStringContainsString('unknown command', $stderr);
    }

    public function testACommandNeedsExactlyOneArgument(): void
    {
        [, , $code] = $this->capture(['normalize']);

        self::assertSame(2, $code);
    }

    public function testABadQueryPairIsRefused(): void
    {
        [, $stderr, $code] = $this->capture(['query', 'https://example.com/', 'novalue=1', 'nope']);

        self::assertSame(2, $code);
        self::assertStringContainsString('expected KEY=VALUE', $stderr);
    }

    public function testHelpExitsZero(): void
    {
        [$stdout, , $code] = $this->capture(['--help']);

        self::assertSame(0, $code);
        self::assertStringContainsString('usage: {{ npm_name }}', $stdout);
    }
}
