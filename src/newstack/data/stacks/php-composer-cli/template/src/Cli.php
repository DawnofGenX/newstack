<?php

declare(strict_types=1);

namespace {{ package_name }};

use {{ package_name }}\Options\Mode;
use {{ package_name }}\Options\Status;

/**
 * The runnable command: turns argv into output and an exit code.
 *
 * Nothing here calls {@code exit}, so tests drive {@see Cli::run()} directly with
 * memory streams. Exit codes: 0 success, 1 unreadable input, 2 bad usage.
 */
final class Cli
{
    public function __construct(private readonly string $program = '{{ npm_name }}')
    {
    }

    /**
     * @param list<string> $args
     * @param resource     $stdin
     * @param resource     $stdout
     * @param resource     $stderr
     */
    public function run(array $args, $stdin, $stdout, $stderr): int
    {
        $options = Options::parse($args);

        switch ($options->status) {
            case Status::HELP:
                fwrite($stdout, Options::usage($this->program));

                return 0;
            case Status::VERSION:
                fwrite($stdout, Options::VERSION . PHP_EOL);

                return 0;
            case Status::ERROR:
                fwrite($stderr, 'error: ' . $options->error . PHP_EOL . PHP_EOL);
                fwrite($stderr, Options::usage($this->program));

                return 2;
            case Status::OK:
                break;
        }

        $mode = $options->mode;
        $files = $options->files;

        if ($files === []) {
            $counts = TextStat::count((string) stream_get_contents($stdin));
            $this->printCounts($stdout, $counts, $mode, '');

            return 0;
        }

        $total = new Counts(0, 0, 0);
        $failed = false;

        foreach ($files as $path) {
            if ($path === '-') {
                $this->printCounts($stdout, TextStat::count((string) stream_get_contents($stdin)), $mode, '');
                continue;
            }
            $contents = @file_get_contents($path);
            if ($contents === false) {
                fwrite($stderr, "error: cannot open '{$path}'" . PHP_EOL);
                $failed = true;
                continue;
            }
            $counts = TextStat::count($contents);
            $this->printCounts($stdout, $counts, $mode, $path);
            $total = $total->plus($counts);
        }

        if (count($files) > 1) {
            $this->printCounts($stdout, $total, $mode, 'total');
        }

        return $failed ? 1 : 0;
    }

    /**
     * @param resource $out
     */
    private function printCounts($out, Counts $counts, Mode $mode, string $label): void
    {
        $line = '';
        if ($mode === Mode::ALL || $mode === Mode::LINES) {
            $line .= sprintf('%8d', $counts->lines);
        }
        if ($mode === Mode::ALL || $mode === Mode::WORDS) {
            $line .= sprintf('%8d', $counts->words);
        }
        if ($mode === Mode::ALL || $mode === Mode::BYTES) {
            $line .= sprintf('%8d', $counts->bytes);
        }
        if ($label !== '') {
            $line .= ' ' . $label;
        }

        fwrite($out, $line . PHP_EOL);
    }
}
