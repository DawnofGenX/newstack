<?php

declare(strict_types=1);

namespace {{ package_name }}\Tests;

use {{ package_name }}\Options;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\TestCase;

final class OptionsTest extends TestCase
{
    public static function modeArguments(): array
    {
        return [
            'default is all' => [[], Options\Mode::ALL],
            'short lines' => [['-l'], Options\Mode::LINES],
            'long lines' => [['--lines'], Options\Mode::LINES],
            'short words' => [['-w'], Options\Mode::WORDS],
            'long words' => [['--words'], Options\Mode::WORDS],
            'short bytes' => [['-c'], Options\Mode::BYTES],
            'long bytes' => [['--bytes'], Options\Mode::BYTES],
        ];
    }

    #[DataProvider('modeArguments')]
    public function testModeIsSelectedByFlag(array $args, Options\Mode $expected): void
    {
        $options = Options::parse($args);

        self::assertSame(Options\Status::OK, $options->status);
        self::assertSame($expected, $options->mode);
        self::assertSame([], $options->files);
    }

    public function testFilesAreCollectedInOrder(): void
    {
        $options = Options::parse(['-w', 'a.txt', 'b.txt']);

        self::assertSame(Options\Status::OK, $options->status);
        self::assertSame(['a.txt', 'b.txt'], $options->files);
    }

    public function testDoubleDashStopsOptionParsing(): void
    {
        $options = Options::parse(['--', '-w']);

        self::assertSame(Options\Status::OK, $options->status);
        self::assertSame(Options\Mode::ALL, $options->mode);
        self::assertSame(['-w'], $options->files);
    }

    public function testDashMeansStandardInput(): void
    {
        $options = Options::parse(['-c', '-']);

        self::assertSame(Options\Status::OK, $options->status);
        self::assertSame(['-'], $options->files);
    }

    public function testHelpFlagWins(): void
    {
        $options = Options::parse(['-l', '--help']);

        self::assertSame(Options\Status::HELP, $options->status);
    }

    public function testVersionFlagWins(): void
    {
        $options = Options::parse(['--version']);

        self::assertSame(Options\Status::VERSION, $options->status);
    }

    public function testUnknownOptionIsAnError(): void
    {
        $options = Options::parse(['--bogus']);

        self::assertSame(Options\Status::ERROR, $options->status);
        self::assertSame("unknown option '--bogus'", $options->error);
    }

    public function testConflictingModesAreAnError(): void
    {
        $options = Options::parse(['-l', '-w']);

        self::assertSame(Options\Status::ERROR, $options->status);
        self::assertStringContainsString('conflicts with an earlier mode', $options->error);
    }

    public function testRepeatingTheSameModeIsAllowed(): void
    {
        $options = Options::parse(['-l', '-l']);

        self::assertSame(Options\Status::OK, $options->status);
        self::assertSame(Options\Mode::LINES, $options->mode);
    }

    public function testUsageNamesTheProgramAndEveryFlag(): void
    {
        $usage = Options::usage('textstat');

        self::assertStringContainsString('usage: textstat', $usage);
        self::assertStringContainsString('--lines', $usage);
        self::assertStringContainsString('--words', $usage);
        self::assertStringContainsString('--bytes', $usage);
        self::assertStringContainsString('--help', $usage);
    }
}
