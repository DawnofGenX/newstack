<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Cli;
use PHPUnit\Framework\TestCase;

final class CliTest extends TestCase
{
    private string $dir;

    protected function setUp(): void
    {
        $this->dir = sys_get_temp_dir() . '/mustache-cli-' . bin2hex(random_bytes(4));
        mkdir($this->dir);
    }

    protected function tearDown(): void
    {
        foreach (glob($this->dir . '/*') ?: [] as $file) {
            unlink($file);
        }
        rmdir($this->dir);
    }

    /** @param list<string> $args */
    private function capture(array $args, string $stdin = ''): array
    {
        $input = fopen('php://memory', 'r+');
        fwrite($input, $stdin);
        rewind($input);
        $out = fopen('php://memory', 'r+');
        $err = fopen('php://memory', 'r+');

        $code = (new Cli('mustache-cli'))->run($args, $input, $out, $err);

        rewind($out);
        rewind($err);
        return [$code, (string) stream_get_contents($out), (string) stream_get_contents($err)];
    }

    public function testRendersWithInlineJson(): void
    {
        [$code, $out] = $this->capture(['template.mustache', '--json', '{"name":"ada"}'], '');
        self::assertSame(1, $code, 'a missing template file is an input error, not a crash');

        $path = $this->write('t.mustache', 'hi {{!name}}');
        [$code, $out] = $this->capture([$path, '--json', '{"name":"ada"}']);
        self::assertSame(0, $code);
        self::assertSame("hi ada\n", $out);
    }

    public function testReadsJsonFromAFile(): void
    {
        $template = $this->write('t.mustache', '{{!#items}}{{!.}},{{!/items}}');
        $data = $this->write('d.json', '{"items":[1,2]}');
        [$code, $out] = $this->capture([$template, '--data', $data]);
        self::assertSame(0, $code);
        self::assertSame("1,2,\n", $out);
    }

    public function testTemplateOnStdinWithDataFlag(): void
    {
        $data = $this->write('d.json', '{"name":"ada"}');
        [$code, $out] = $this->capture(['--data', $data], 'hi {{!name}}');
        self::assertSame(0, $code);
        self::assertSame("hi ada\n", $out);
    }

    public function testInvalidJsonExitsOne(): void
    {
        $path = $this->write('t.mustache', 'hi');
        [$code, , $err] = $this->capture([$path, '--json', '{oops']);
        self::assertSame(1, $code);
        self::assertStringContainsString('invalid JSON', $err);
    }

    public function testTemplateErrorExitsOne(): void
    {
        $path = $this->write('t.mustache', '{{!#a}}x');
        [$code, , $err] = $this->capture([$path, '--json', '{}']);
        self::assertSame(1, $code);
        self::assertStringContainsString('never closed', $err);
    }

    public function testUnknownOptionExitsTwo(): void
    {
        [$code, , $err] = $this->capture(['--bogus']);
        self::assertSame(2, $code);
        self::assertStringContainsString('unknown option', $err);
    }

    public function testHelpExitsZero(): void
    {
        [$code, $out] = $this->capture(['--help']);
        self::assertSame(0, $code);
        self::assertStringContainsString('usage: mustache-cli', $out);
    }

    private function write(string $name, string $contents): string
    {
        $path = $this->dir . '/' . $name;
        file_put_contents($path, $contents);
        return $path;
    }
}
