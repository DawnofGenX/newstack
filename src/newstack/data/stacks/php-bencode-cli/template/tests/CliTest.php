<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use PHPUnit\Framework\TestCase;
use {{ package_name }}\Cli;

final class CliTest extends TestCase
{
    /** @return array{0: int, 1: string, 2: string} */
    private function capture(array $argv, string $stdin = ''): array
    {
        $in = fopen('php://memory', 'r+');
        fwrite($in, $stdin);
        rewind($in);
        $out = fopen('php://memory', 'r+');
        $err = fopen('php://memory', 'r+');

        $status = (new Cli('bencode'))->run($argv, $in, $out, $err);

        rewind($out);
        rewind($err);

        return [$status, (string) stream_get_contents($out), (string) stream_get_contents($err)];
    }

    public function test_encode_reads_json_from_stdin(): void
    {
        [$status, $stdout] = $this->capture(['encode'], '{"a":1,"b":["x"]}');

        self::assertSame(0, $status);
        self::assertSame("d1:ai1e1:bl1:xee\n", $stdout);
    }

    public function test_decode_writes_json(): void
    {
        [$status, $stdout] = $this->capture(['decode'], 'd1:ai1e1:bl1:xee');

        self::assertSame(0, $status);
        self::assertSame("{\"a\":1,\"b\":[\"x\"]}\n", $stdout);
    }

    public function test_encode_round_trips_through_decode(): void
    {
        [$status, $encoded] = $this->capture(['encode'], '{"list":[1,2,{"k":"v"}]}');
        self::assertSame(0, $status);

        [$status, $decoded] = $this->capture(['decode'], $encoded);
        self::assertSame(0, $status);
        self::assertSame('{"list":[1,2,{"k":"v"}]}', trim($decoded));
    }

    public function test_invalid_json_exits_1(): void
    {
        [$status, , $stderr] = $this->capture(['encode'], 'not json');

        self::assertSame(1, $status);
        self::assertStringContainsString('bencode:', $stderr);
    }

    public function test_invalid_bencode_exits_1(): void
    {
        [$status, , $stderr] = $this->capture(['decode'], 'i03e');

        self::assertSame(1, $status);
        self::assertStringContainsString('malformed integer', $stderr);
    }

    public function test_a_missing_command_exits_2(): void
    {
        [$status, , $stderr] = $this->capture([]);

        self::assertSame(2, $status);
        self::assertStringContainsString('a command is required', $stderr);
    }

    public function test_an_unknown_command_exits_2(): void
    {
        [$status] = $this->capture(['frobnicate']);

        self::assertSame(2, $status);
    }

    public function test_too_many_paths_is_a_usage_error(): void
    {
        [$status] = $this->capture(['encode', 'a.json', 'b.json']);

        self::assertSame(2, $status);
    }

    public function test_a_missing_file_exits_1(): void
    {
        [$status, , $stderr] = $this->capture(['encode', 'does-not-exist.json']);

        self::assertSame(1, $status);
        self::assertStringContainsString('cannot read', $stderr);
    }

    public function test_help_exits_0(): void
    {
        [$status, $stdout] = $this->capture(['--help']);

        self::assertSame(0, $status);
        self::assertStringContainsString('Bencode encoder/decoder', $stdout);
    }
}
