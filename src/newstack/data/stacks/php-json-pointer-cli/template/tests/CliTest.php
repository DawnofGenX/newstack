<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use PHPUnit\Framework\TestCase;
use {{ package_name }}\Cli;

final class CliTest extends TestCase
{
    private const DOC = '{"name":"demo","tags":["a","b"],"nested":{"id":3}}';

    /** @return array{0:int,1:string,2:string} */
    private function capture(array $args, string $stdin = self::DOC): array
    {
        $in = fopen('php://memory', 'r+');
        fwrite($in, $stdin);
        rewind($in);
        $out = fopen('php://memory', 'r+');
        $err = fopen('php://memory', 'r+');

        $code = (new Cli('jsonptr'))->run($args, $in, $out, $err);

        rewind($out);
        rewind($err);

        return [$code, (string) stream_get_contents($out), (string) stream_get_contents($err)];
    }

    public function testGetPrintsJson(): void
    {
        [$code, $out] = $this->capture(['get', '/nested/id']);
        self::assertSame(0, $code);
        self::assertSame("3\n", $out);
    }

    public function testGetOnMissingPointerExitsOne(): void
    {
        [$code, , $err] = $this->capture(['get', '/nope']);
        self::assertSame(1, $code);
        self::assertStringContainsString("no such member 'nope'", $err);
    }

    public function testSetWritesTheDocumentBack(): void
    {
        [$code, $out] = $this->capture(['set', '/name', '--value', '"renamed"']);
        self::assertSame(0, $code);
        self::assertStringContainsString('"name":"renamed"', $out);
    }

    public function testSetWithoutValueExitsTwo(): void
    {
        [$code, , $err] = $this->capture(['set', '/name']);
        self::assertSame(2, $code);
        self::assertStringContainsString('set needs --value', $err);
    }

    public function testRemovePrintsTheRemovedValue(): void
    {
        [$code, $out] = $this->capture(['remove', '/tags/0']);
        self::assertSame(0, $code);
        self::assertStringContainsString('"removed":"a"', $out);
        self::assertStringContainsString('"tags":["b"]', $out);
    }

    public function testHasUsesTheExitCode(): void
    {
        self::assertSame(0, $this->capture(['has', '/tags/1'])[0]);
        self::assertSame(1, $this->capture(['has', '/tags/9'])[0]);
    }

    public function testTokensPrintsTheDecodedList(): void
    {
        [$code, $out] = $this->capture(['tokens', '/a~1b/m~0n']);
        self::assertSame(0, $code);
        self::assertSame('["a/b","m~n"]' . PHP_EOL, $out);
    }

    public function testRejectsUnknownCommandAndOption(): void
    {
        self::assertSame(2, $this->capture(['frobnicate'])[0]);
        self::assertSame(2, $this->capture(['get', '/name', '--bogus'])[0]);
    }

    public function testHelpExitsZero(): void
    {
        [$code, $out] = $this->capture(['--help']);
        self::assertSame(0, $code);
        self::assertStringContainsString('Usage: jsonptr', $out);
    }

    public function testInvalidJsonExitsOne(): void
    {
        [$code, , $err] = $this->capture(['get', '/name'], 'not json');
        self::assertSame(1, $code);
        self::assertStringContainsString('invalid JSON', $err);
    }
}
