<?php

declare(strict_types=1);

namespace {{ package_name }};

use {{ package_name }}\Options\Mode;
use {{ package_name }}\Options\Status;

/**
 * Parsed command line: the chosen mode, the files, and how parsing ended.
 *
 * Hand-rolled on purpose — no dependency, and every branch is unit tested.
 */
final class Options
{
    public const VERSION = '0.1.0';

    /**
     * @param list<string> $files
     */
    private function __construct(
        public readonly Mode $mode,
        public readonly array $files,
        public readonly Status $status,
        public readonly string $error,
    ) {
    }

    /**
     * @param list<string> $args
     */
    public static function parse(array $args): self
    {
        $chosen = null;
        $onlyFiles = false;
        $files = [];

        foreach ($args as $arg) {
            $arg = (string) $arg;
            if ($onlyFiles || $arg === '' || $arg === '-') {
                $files[] = $arg;
                continue;
            }
            if ($arg === '--') {
                $onlyFiles = true;
                continue;
            }
            if ($arg === '-h' || $arg === '--help') {
                return new self($chosen ?? Mode::ALL, $files, Status::HELP, '');
            }
            if ($arg === '-V' || $arg === '--version') {
                return new self($chosen ?? Mode::ALL, $files, Status::VERSION, '');
            }
            $requested = self::modeFor($arg);
            if ($requested !== null) {
                if ($chosen !== null && $chosen !== $requested) {
                    return new self(
                        $chosen,
                        $files,
                        Status::ERROR,
                        "choose one of -l, -w, -c: '{$arg}' conflicts with an earlier mode",
                    );
                }
                $chosen = $requested;
                continue;
            }
            if (str_starts_with($arg, '-')) {
                return new self($chosen ?? Mode::ALL, $files, Status::ERROR, "unknown option '{$arg}'");
            }
            $files[] = $arg;
        }

        return new self($chosen ?? Mode::ALL, $files, Status::OK, '');
    }

    private static function modeFor(string $arg): ?Mode
    {
        return match ($arg) {
            '-l', '--lines' => Mode::LINES,
            '-w', '--words' => Mode::WORDS,
            '-c', '--bytes' => Mode::BYTES,
            default => null,
        };
    }

    /** Help text; the program name comes from the caller so it matches the entry point. */
    public static function usage(string $program): string
    {
        return "usage: {$program} [-l | -w | -c] [--] [FILE ...]\n"
            . "\n"
            . "Count lines, words and bytes in each FILE, or in standard input\n"
            . "when no FILE is given. With more than one FILE a total is printed.\n"
            . "\n"
            . "  -l, --lines     print the line count only\n"
            . "  -w, --words     print the word count only\n"
            . "  -c, --bytes     print the byte count only\n"
            . "  -h, --help      show this help and exit\n"
            . "  -V, --version   show the version and exit\n";
    }
}
